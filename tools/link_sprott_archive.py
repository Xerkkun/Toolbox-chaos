#!/usr/bin/env python3
"""
Create a locally navigable HTML view for a downloaded Sprott archive.

The downloader keeps the original saved pages under ``pages/`` and downloaded
assets under ``files/``. This script reads ``manifest.csv`` and writes rewritten
HTML files under ``browse/`` so local links point to the downloaded copies.
"""

from __future__ import annotations

import argparse
import csv
import html
import os
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path


LOCAL_STATUSES = {"downloaded", "skipped_exists"}
PAGE_STATUS = "page_saved"
SKIP_SCHEMES = {"mailto", "tel", "javascript", "data", "news", "ftp"}
REWRITABLE_ATTRS = {"href", "src", "poster", "data", "background"}

ATTR_RE = re.compile(
    r"(?P<prefix>\b(?P<attr>href|src|poster|data|background)\s*=\s*)"
    r"(?P<quote>[\"'])"
    r"(?P<value>.*?)"
    r"(?P=quote)",
    re.IGNORECASE | re.DOTALL,
)

SRCSET_RE = re.compile(
    r"(?P<prefix>\bsrcset\s*=\s*)"
    r"(?P<quote>[\"'])"
    r"(?P<value>.*?)"
    r"(?P=quote)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class LocalTarget:
    url: str
    path: Path
    kind: str


@dataclass
class RewriteStats:
    pages_written: int = 0
    html_links_rewritten: int = 0
    file_links_rewritten: int = 0
    external_links_updated: int = 0
    srcset_entries_rewritten: int = 0
    local_targets_missing: int = 0


def canonical_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    parsed = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        fragment="",
    )
    return urllib.parse.urlunparse(parsed)


def split_fragment(url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(url)
    fragment = parsed.fragment
    without_fragment = urllib.parse.urlunparse(parsed._replace(fragment=""))
    return without_fragment, fragment


def wayback_embedded_url(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc.lower() != "web.archive.org":
        return None

    match = re.search(r"/web/\d+/(https?://.+)$", parsed.path)
    if not match:
        return None
    return match.group(1)


def browser_href(from_path: Path, target_path: Path, fragment: str = "") -> str:
    rel = os.path.relpath(target_path, start=from_path.parent)
    href = Path(rel).as_posix()
    if fragment:
        href = f"{href}#{fragment}"
    return html.escape(href, quote=True)


def read_manifest(archive_dir: Path) -> list[dict[str, str]]:
    manifest_path = archive_dir / "manifest.csv"
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")

    with manifest_path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_url_replacements(archive_dir: Path) -> dict[str, str]:
    lookup_path = archive_dir / "tycho_course_lookup.csv"
    if not lookup_path.exists():
        return {}

    replacements: dict[str, str] = {}
    with lookup_path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            source_url = (row.get("source_url") or "").strip()
            live_url = (row.get("live_candidate") or "").strip()
            archive_url = (row.get("archive_url") or "").strip()
            if row.get("live_status") == "found" and source_url and live_url:
                replacements[canonical_url(source_url)] = live_url
            elif source_url and archive_url:
                replacements[canonical_url(source_url)] = archive_url
    return replacements


def add_page_aliases(targets: dict[str, LocalTarget], target: LocalTarget) -> None:
    parsed = urllib.parse.urlparse(target.url)
    if parsed.path.endswith("/"):
        for index_name in ("index.html", "index.htm"):
            alias = urllib.parse.urlunparse(parsed._replace(path=f"{parsed.path}{index_name}"))
            targets.setdefault(canonical_url(alias), target)
    elif parsed.path.lower().endswith(("/index.html", "/index.htm")):
        base_path = parsed.path.rsplit("/", 1)[0] + "/"
        alias = urllib.parse.urlunparse(parsed._replace(path=base_path))
        targets.setdefault(canonical_url(alias), target)


def build_targets(
    rows: list[dict[str, str]],
    pages_dir: Path,
    browse_dir: Path,
) -> tuple[dict[str, LocalTarget], dict[str, LocalTarget], list[LocalTarget]]:
    page_targets: dict[str, LocalTarget] = {}
    file_targets: dict[str, LocalTarget] = {}
    pages: list[LocalTarget] = []
    page_output_paths_seen: set[str] = set()

    for row in rows:
        url = (row.get("url") or "").strip()
        local_path = (row.get("local_path") or "").strip()
        status = (row.get("status") or "").strip()
        if not url or not local_path:
            continue

        path = Path(local_path)
        if status == PAGE_STATUS and path.exists():
            try:
                rel_path = path.resolve().relative_to(pages_dir.resolve())
            except ValueError:
                rel_path = Path(path.name)
            browse_path = browse_dir / rel_path
            target = LocalTarget(url=canonical_url(url), path=browse_path, kind="page")
            page_targets[target.url] = target
            add_page_aliases(page_targets, target)
            output_key = str(browse_path.resolve()).lower()
            if output_key not in page_output_paths_seen:
                pages.append(target)
                page_output_paths_seen.add(output_key)
        elif status in LOCAL_STATUSES and path.exists():
            target = LocalTarget(url=canonical_url(url), path=path, kind="file")
            file_targets[target.url] = target

    pages.sort(key=lambda item: item.path.as_posix().lower())
    return page_targets, file_targets, pages


def resolve_local_target(
    *,
    page_url: str,
    raw_value: str,
    current_output: Path,
    page_targets: dict[str, LocalTarget],
    file_targets: dict[str, LocalTarget],
    url_replacements: dict[str, str],
    stats: RewriteStats,
) -> str | None:
    value = html.unescape(raw_value).strip()
    if not value:
        return None

    parsed_value = urllib.parse.urlparse(value)
    if parsed_value.scheme.lower() in SKIP_SCHEMES:
        return None

    absolute = urllib.parse.urljoin(page_url, value)
    no_fragment, fragment = split_fragment(absolute)
    key = canonical_url(no_fragment)

    if key in page_targets:
        stats.html_links_rewritten += 1
        return browser_href(current_output, page_targets[key].path, fragment)

    if key in file_targets:
        stats.file_links_rewritten += 1
        return browser_href(current_output, file_targets[key].path, fragment)

    if key in url_replacements:
        stats.external_links_updated += 1
        return html.escape(url_replacements[key], quote=True)

    embedded_url = wayback_embedded_url(absolute)
    if embedded_url:
        embedded_key = canonical_url(embedded_url)
        if embedded_key in url_replacements:
            stats.external_links_updated += 1
            return html.escape(url_replacements[embedded_key], quote=True)

    if urllib.parse.urlparse(key).netloc == urllib.parse.urlparse(page_url).netloc:
        stats.local_targets_missing += 1
    return None


def rewrite_srcset(
    *,
    value: str,
    page_url: str,
    current_output: Path,
    page_targets: dict[str, LocalTarget],
    file_targets: dict[str, LocalTarget],
    url_replacements: dict[str, str],
    stats: RewriteStats,
) -> str:
    parts: list[str] = []
    changed = False
    for raw_candidate in value.split(","):
        candidate = raw_candidate.strip()
        if not candidate:
            continue
        tokens = candidate.split()
        rewritten = resolve_local_target(
            page_url=page_url,
            raw_value=tokens[0],
            current_output=current_output,
            page_targets=page_targets,
            file_targets=file_targets,
            url_replacements=url_replacements,
            stats=stats,
        )
        if rewritten:
            tokens[0] = rewritten
            stats.srcset_entries_rewritten += 1
            changed = True
        parts.append(" ".join(tokens))
    return ", ".join(parts) if changed else value


def rewrite_html(
    *,
    source_html: str,
    page_url: str,
    current_output: Path,
    page_targets: dict[str, LocalTarget],
    file_targets: dict[str, LocalTarget],
    url_replacements: dict[str, str],
    stats: RewriteStats,
) -> str:
    def replace_attr(match: re.Match[str]) -> str:
        attr = match.group("attr").lower()
        quote = match.group("quote")
        value = match.group("value")
        if attr not in REWRITABLE_ATTRS:
            return match.group(0)

        rewritten = resolve_local_target(
            page_url=page_url,
            raw_value=value,
            current_output=current_output,
            page_targets=page_targets,
            file_targets=file_targets,
            url_replacements=url_replacements,
            stats=stats,
        )
        if not rewritten:
            return match.group(0)
        return f"{match.group('prefix')}{quote}{rewritten}{quote}"

    def replace_srcset(match: re.Match[str]) -> str:
        quote = match.group("quote")
        value = match.group("value")
        rewritten = rewrite_srcset(
            value=value,
            page_url=page_url,
            current_output=current_output,
            page_targets=page_targets,
            file_targets=file_targets,
            url_replacements=url_replacements,
            stats=stats,
        )
        if rewritten == value:
            return match.group(0)
        return f"{match.group('prefix')}{quote}{html.escape(rewritten, quote=True)}{quote}"

    rewritten_html = ATTR_RE.sub(replace_attr, source_html)
    return SRCSET_RE.sub(replace_srcset, rewritten_html)


def extract_title(page_path: Path) -> str:
    try:
        text = page_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return page_path.name
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return page_path.name
    title = re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()
    return title or page_path.name


def write_archive_index(
    *,
    archive_dir: Path,
    browse_dir: Path,
    pages_dir: Path,
    pages: list[LocalTarget],
    stats: RewriteStats,
) -> None:
    index_path = browse_dir / "_archive_index.html"
    items: list[str] = []
    for page in pages:
        try:
            page_rel = page.path.resolve().relative_to(browse_dir.resolve())
            original_rel = (pages_dir / page_rel).resolve()
        except ValueError:
            page_rel = Path(page.path.name)
            original_rel = pages_dir / page.path.name
        title = extract_title(original_rel)
        href = html.escape(page_rel.as_posix(), quote=True)
        label = html.escape(title)
        url = html.escape(page.url)
        items.append(f'<li><a href="{href}">{label}</a><br><small>{url}</small></li>')

    body = "\n".join(items)
    content = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Sprott local archive index</title>
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.4; margin: 2rem; max-width: 1100px; }}
    code, small {{ color: #555; }}
    li {{ margin: 0.45rem 0; }}
  </style>
</head>
<body>
  <h1>Sprott local archive index</h1>
  <p>Archivo local generado desde <code>{html.escape(archive_dir.name)}</code>.</p>
    <p>
    Paginas HTML: {stats.pages_written} | enlaces a paginas reescritos: {stats.html_links_rewritten} |
    enlaces a archivos reescritos: {stats.file_links_rewritten} |
    enlaces externos actualizados: {stats.external_links_updated} | entradas srcset: {stats.srcset_entries_rewritten}
  </p>
  <ol>
{body}
  </ol>
</body>
</html>
"""
    index_path.write_text(content, encoding="utf-8", newline="\n")


def link_archive(archive_dir: Path) -> RewriteStats:
    archive_dir = archive_dir.resolve()
    pages_dir = archive_dir / "pages"
    browse_dir = archive_dir / "browse"
    rows = read_manifest(archive_dir)
    page_targets, file_targets, pages = build_targets(rows, pages_dir, browse_dir)
    url_replacements = load_url_replacements(archive_dir)

    stats = RewriteStats()
    for page in pages:
        try:
            page_rel = page.path.resolve().relative_to(browse_dir.resolve())
        except ValueError:
            page_rel = Path(page.path.name)
        source_path = pages_dir / page_rel
        if not source_path.exists():
            continue

        source_html = source_path.read_text(encoding="utf-8", errors="ignore")
        rewritten = rewrite_html(
            source_html=source_html,
            page_url=page.url,
            current_output=page.path,
            page_targets=page_targets,
            file_targets=file_targets,
            url_replacements=url_replacements,
            stats=stats,
        )
        page.path.parent.mkdir(parents=True, exist_ok=True)
        page.path.write_text(rewritten, encoding="utf-8", newline="")
        stats.pages_written += 1

    browse_dir.mkdir(parents=True, exist_ok=True)
    write_archive_index(
        archive_dir=archive_dir,
        browse_dir=browse_dir,
        pages_dir=pages_dir,
        pages=pages,
        stats=stats,
    )
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rewrite downloaded Sprott HTML pages to use local files."
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("external/sprott_site_theory"),
        help="Archive directory containing manifest.csv, pages/, and files/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stats = link_archive(args.archive)
    browse_dir = args.archive.resolve() / "browse"
    print(f"Browse directory: {browse_dir}")
    print(f"Pages written: {stats.pages_written}")
    print(f"HTML page links rewritten: {stats.html_links_rewritten}")
    print(f"File/image links rewritten: {stats.file_links_rewritten}")
    print(f"External links updated: {stats.external_links_updated}")
    print(f"srcset entries rewritten: {stats.srcset_entries_rewritten}")
    print(f"Same-site targets not in manifest: {stats.local_targets_missing}")
    print(f"Archive index: {browse_dir / '_archive_index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
