#!/usr/bin/env python3
"""
Download and organize downloadable material from Sprott's website.

Purpose:
    Local research archive for studying J. C. Sprott's publicly linked material.

Default behavior:
    - Starts at https://sprott.physics.wisc.edu/
    - Crawls same-domain HTML pages.
    - Downloads linked non-HTML files.
    - Preserves remote path structure locally.
    - Writes manifest CSV and JSONL.
    - Respects robots.txt when available.
    - Uses a delay between requests.

Important:
    Do not commit downloaded files to this repository unless you have permission
    and the licensing terms are compatible with your project.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_START_URL = "https://sprott.physics.wisc.edu/"

HTML_EXTENSIONS = {
    "",
    ".html",
    ".htm",
    ".shtml",
    ".asp",
    ".aspx",
    ".php",
    ".cgi",
}

DOWNLOAD_EXTENSIONS = {
    ".zip",
    ".gz",
    ".tgz",
    ".tar",
    ".rar",
    ".7z",
    ".bz2",
    ".exe",
    ".dll",
    ".com",
    ".bat",
    ".sys",
    ".msi",
    ".bas",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".f",
    ".for",
    ".f90",
    ".py",
    ".m",
    ".java",
    ".js",
    ".vb",
    ".vbs",
    ".pl",
    ".sh",
    ".dic",
    ".mrg",
    ".mac",
    ".dat",
    ".txt",
    ".csv",
    ".tsv",
    ".ini",
    ".cfg",
    ".json",
    ".xml",
    ".pdf",
    ".doc",
    ".docx",
    ".rtf",
    ".ps",
    ".eps",
    ".tex",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".gif",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".ico",
    ".svg",
    ".webp",
    ".mid",
    ".midi",
    ".mp3",
    ".wav",
    ".au",
    ".aif",
    ".aiff",
    ".ogg",
    ".flac",
    ".mp4",
    ".mpg",
    ".mpeg",
    ".avi",
    ".mov",
    ".wmv",
    ".webm",
    ".m4v",
}

IMAGE_EXTENSIONS = {
    ".gif",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".ico",
    ".svg",
    ".webp",
}


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value for key, value in attrs if value}
        for key in ("href", "src"):
            value = attrs_dict.get(key)
            if value:
                self.links.append(value)


@dataclass
class DownloadRecord:
    url: str
    local_path: str
    status: str
    http_status: int | None
    content_type: str | None
    size_bytes: int
    sha256: str | None
    error: str | None


def normalize_url(base_url: str, link: str) -> str | None:
    link = link.strip()
    if not link:
        return None

    lowered = link.lower()
    if lowered.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None

    absolute = urllib.parse.urljoin(base_url, link)
    parsed = urllib.parse.urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return None

    parsed = parsed._replace(fragment="")
    return urllib.parse.urlunparse(parsed)


def same_site(url: str, allowed_netloc: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc.lower() == allowed_netloc.lower()


def under_path_prefix(url: str, path_prefix: str) -> bool:
    path = urllib.parse.urlparse(url).path
    return path.startswith(path_prefix)


def extension_from_url(url: str) -> str:
    return Path(urllib.parse.urlparse(url).path).suffix.lower()


def looks_like_html(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return extension_from_url(url) in HTML_EXTENSIONS or parsed.path.endswith("/")


def looks_downloadable(
    url: str,
    download_unknown: bool = False,
    include_extensions: set[str] | None = None,
    exclude_extensions: set[str] | None = None,
) -> bool:
    ext = extension_from_url(url)
    if include_extensions is not None:
        return ext in include_extensions
    if exclude_extensions is not None and ext in exclude_extensions:
        return False
    if ext in DOWNLOAD_EXTENSIONS:
        return True
    if ext in HTML_EXTENSIONS:
        return False
    return download_unknown


def parse_extension_list(value: str | None) -> set[str] | None:
    if value is None:
        return None

    out: set[str] = set()
    for item in value.split(","):
        ext = item.strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = "." + ext
        out.add(ext)
    return out


def safe_local_path(output_dir: Path, url: str, subdir: str) -> Path:
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.unquote(parsed.path)
    if not path or path.endswith("/"):
        path = path + "index.html"

    relative = path.lstrip("/")
    relative = re.sub(r'[<>:"|?*]', "_", relative)

    if parsed.query:
        query_hash = hashlib.sha256(parsed.query.encode("utf-8")).hexdigest()[:12]
        p = Path(relative)
        relative = str(p.with_name(f"{p.stem}_{query_hash}{p.suffix}"))

    local_path = output_dir / subdir / relative
    local_path.parent.mkdir(parents=True, exist_ok=True)
    return local_path


def open_request(url: str, user_agent: str, timeout: float) -> tuple[int | None, str | None, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent}, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", None)
        content_type = response.headers.get("Content-Type")
        data = response.read()
        return status, content_type, data


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(
    url: str,
    output_dir: Path,
    user_agent: str,
    timeout: float,
    overwrite: bool,
) -> DownloadRecord:
    local_path = safe_local_path(output_dir, url, subdir="files")

    if local_path.exists() and not overwrite:
        return DownloadRecord(
            url=url,
            local_path=str(local_path),
            status="skipped_exists",
            http_status=None,
            content_type=None,
            size_bytes=local_path.stat().st_size,
            sha256=sha256_file(local_path),
            error=None,
        )

    try:
        http_status, content_type, data = open_request(url, user_agent, timeout)
        local_path.write_bytes(data)
        return DownloadRecord(
            url=url,
            local_path=str(local_path),
            status="downloaded",
            http_status=http_status,
            content_type=content_type,
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            error=None,
        )
    except Exception as exc:
        return DownloadRecord(
            url=url,
            local_path=str(local_path),
            status="error",
            http_status=None,
            content_type=None,
            size_bytes=0,
            sha256=None,
            error=repr(exc),
        )


def save_html_page(url: str, html: bytes, output_dir: Path) -> Path:
    local_path = safe_local_path(output_dir, url, subdir="pages")
    local_path.write_bytes(html)
    return local_path


def load_robots(start_url: str) -> urllib.robotparser.RobotFileParser:
    parsed = urllib.parse.urlparse(start_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    robots = urllib.robotparser.RobotFileParser()
    robots.set_url(robots_url)
    try:
        robots.read()
    except Exception:
        robots.allow_all = True
    return robots


def write_manifest(output_dir: Path, records: list[DownloadRecord]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "manifest.csv"
    jsonl_path = output_dir / "manifest.jsonl"
    fieldnames = [
        "url",
        "local_path",
        "status",
        "http_status",
        "content_type",
        "size_bytes",
        "sha256",
        "error",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))

    with jsonl_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def load_manifest(output_dir: Path) -> list[DownloadRecord]:
    csv_path = output_dir / "manifest.csv"
    if not csv_path.exists():
        return []

    records: list[DownloadRecord] = []
    with csv_path.open("r", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            records.append(
                DownloadRecord(
                    url=row.get("url", ""),
                    local_path=row.get("local_path", ""),
                    status=row.get("status", ""),
                    http_status=int(row["http_status"]) if row.get("http_status") else None,
                    content_type=row.get("content_type") or None,
                    size_bytes=int(row["size_bytes"]) if row.get("size_bytes") else 0,
                    sha256=row.get("sha256") or None,
                    error=row.get("error") or None,
                )
            )
    return records


def upsert_record(records_by_url: dict[str, DownloadRecord], record: DownloadRecord) -> None:
    records_by_url[record.url] = record


def download_assets_from_manifest(
    output_dir: Path,
    *,
    max_files: int,
    delay: float,
    timeout: float,
    user_agent: str,
    overwrite: bool,
    include_extensions: set[str] | None,
    exclude_extensions: set[str] | None,
    download_unknown: bool,
) -> list[DownloadRecord]:
    existing_records = load_manifest(output_dir)
    records_by_url = {record.url: record for record in existing_records if record.url}
    seen_files: set[str] = {
        record.url
        for record in existing_records
        if record.url and record.status in {"downloaded", "skipped_exists", "dry_run"}
    }
    page_records = [
        record
        for record in existing_records
        if record.status == "page_saved" and record.local_path and Path(record.local_path).exists()
    ]

    downloaded_this_run = 0
    asset_extensions = include_extensions if include_extensions is not None else IMAGE_EXTENSIONS

    def current_records() -> list[DownloadRecord]:
        return list(records_by_url.values())

    try:
        for page_record in page_records:
            if downloaded_this_run >= max_files:
                break

            page_path = Path(page_record.local_path)
            try:
                html = page_path.read_bytes().decode("utf-8", errors="ignore")
            except Exception as exc:
                upsert_record(
                    records_by_url,
                    DownloadRecord(
                        url=page_record.url,
                        local_path=page_record.local_path,
                        status="page_asset_parse_error",
                        http_status=page_record.http_status,
                        content_type=page_record.content_type,
                        size_bytes=page_record.size_bytes,
                        sha256=page_record.sha256,
                        error=repr(exc),
                    ),
                )
                write_manifest(output_dir, current_records())
                continue

            parser = LinkExtractor()
            try:
                parser.feed(html)
            except Exception:
                continue

            allowed_netloc = urllib.parse.urlparse(page_record.url).netloc
            for raw_link in parser.links:
                if downloaded_this_run >= max_files:
                    break

                url = normalize_url(page_record.url, raw_link)
                if not url or not same_site(url, allowed_netloc):
                    continue
                if url in seen_files:
                    continue
                if not looks_downloadable(
                    url,
                    download_unknown=download_unknown,
                    include_extensions=asset_extensions,
                    exclude_extensions=exclude_extensions,
                ):
                    continue

                seen_files.add(url)
                downloaded_this_run += 1
                print(f"[asset {downloaded_this_run}] {url}")
                record = download_file(
                    url,
                    output_dir,
                    user_agent=user_agent,
                    timeout=timeout,
                    overwrite=overwrite,
                )
                upsert_record(records_by_url, record)
                write_manifest(output_dir, current_records())
                time.sleep(delay)
    finally:
        write_manifest(output_dir, current_records())

    return current_records()


def crawl(
    start_url: str,
    output_dir: Path,
    *,
    max_pages: int,
    max_files: int,
    delay: float,
    timeout: float,
    user_agent: str,
    save_pages: bool,
    overwrite: bool,
    download_unknown: bool,
    include_extensions: set[str] | None,
    exclude_extensions: set[str] | None,
    stay_under_start_path: bool,
    dry_run: bool,
) -> list[DownloadRecord]:
    parsed_start = urllib.parse.urlparse(start_url)
    allowed_netloc = parsed_start.netloc
    path_prefix = parsed_start.path
    if not path_prefix.endswith("/"):
        path_prefix = str(Path(path_prefix).parent).replace("\\", "/")
        if not path_prefix.endswith("/"):
            path_prefix += "/"
    robots = load_robots(start_url)

    queue: list[str] = [start_url]
    seen_pages: set[str] = set()
    existing_records = load_manifest(output_dir)
    records_by_url = {record.url: record for record in existing_records if record.url}
    seen_files: set[str] = {
        record.url
        for record in existing_records
        if record.url and record.status in {"downloaded", "skipped_exists", "dry_run"}
    }
    files_seen_this_run = 0

    def current_records() -> list[DownloadRecord]:
        return list(records_by_url.values())

    try:
        while queue and len(seen_pages) < max_pages and files_seen_this_run < max_files:
            page_url = queue.pop(0)
            if page_url in seen_pages:
                continue
            if not same_site(page_url, allowed_netloc):
                continue
            if stay_under_start_path and not under_path_prefix(page_url, path_prefix):
                continue
            if not robots.can_fetch(user_agent, page_url):
                print(f"[robots] skip page: {page_url}")
                continue

            seen_pages.add(page_url)
            print(f"[page {len(seen_pages)}] {page_url}")

            try:
                status, content_type, data = open_request(page_url, user_agent, timeout)
            except Exception as exc:
                upsert_record(
                    records_by_url,
                    DownloadRecord(
                        url=page_url,
                        local_path="",
                        status="page_error",
                        http_status=None,
                        content_type=None,
                        size_bytes=0,
                        sha256=None,
                        error=repr(exc),
                    ),
                )
                write_manifest(output_dir, current_records())
                time.sleep(delay)
                continue

            if save_pages:
                local_page = save_html_page(page_url, data, output_dir)
                upsert_record(
                    records_by_url,
                    DownloadRecord(
                        url=page_url,
                        local_path=str(local_page),
                        status="page_saved",
                        http_status=status,
                        content_type=content_type,
                        size_bytes=len(data),
                        sha256=hashlib.sha256(data).hexdigest(),
                        error=None,
                    ),
                )
                write_manifest(output_dir, current_records())

            content_type = (content_type or "").lower()
            if "html" not in content_type and not looks_like_html(page_url):
                time.sleep(delay)
                continue

            parser = LinkExtractor()
            try:
                parser.feed(data.decode("utf-8", errors="ignore"))
            except Exception:
                time.sleep(delay)
                continue

            for raw_link in parser.links:
                url = normalize_url(page_url, raw_link)
                if not url or not same_site(url, allowed_netloc):
                    continue
                if stay_under_start_path and not under_path_prefix(url, path_prefix):
                    continue

                if looks_like_html(url):
                    if url not in seen_pages and len(seen_pages) + len(queue) < max_pages:
                        queue.append(url)
                    continue

                if not looks_downloadable(
                    url,
                    download_unknown=download_unknown,
                    include_extensions=include_extensions,
                    exclude_extensions=exclude_extensions,
                ):
                    continue
                if url in seen_files:
                    continue
                if files_seen_this_run >= max_files:
                    break
                if not robots.can_fetch(user_agent, url):
                    print(f"[robots] skip file: {url}")
                    continue

                seen_files.add(url)
                files_seen_this_run += 1
                print(f"  [file {files_seen_this_run}] {url}")

                if dry_run:
                    record = DownloadRecord(
                        url=url,
                        local_path=str(safe_local_path(output_dir, url, subdir="files")),
                        status="dry_run",
                        http_status=None,
                        content_type=None,
                        size_bytes=0,
                        sha256=None,
                        error=None,
                    )
                else:
                    record = download_file(
                        url,
                        output_dir,
                        user_agent=user_agent,
                        timeout=timeout,
                        overwrite=overwrite,
                    )
                upsert_record(records_by_url, record)
                write_manifest(output_dir, current_records())
                time.sleep(delay)

            time.sleep(delay)
    finally:
        write_manifest(output_dir, current_records())

    return current_records()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download linked downloadable files from Sprott's website."
    )
    parser.add_argument("--start", default=DEFAULT_START_URL, help=f"Start URL. Default: {DEFAULT_START_URL}")
    parser.add_argument("--output", default="external/sprott_site", help="Output directory.")
    parser.add_argument("--max-pages", type=int, default=3000, help="Maximum HTML pages to crawl.")
    parser.add_argument("--max-files", type=int, default=20000, help="Maximum files to download.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds.")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds.")
    parser.add_argument("--save-pages", action="store_true", help="Save crawled HTML pages under output/pages.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite files already downloaded.")
    parser.add_argument(
        "--download-assets-from-manifest",
        action="store_true",
        help="Read saved HTML pages from manifest.csv and download their linked image assets.",
    )
    parser.add_argument(
        "--download-unknown",
        action="store_true",
        help="Download same-domain links with unknown or nonstandard extensions.",
    )
    parser.add_argument(
        "--include-ext",
        help="Comma-separated extension allowlist for file downloads, for example: .pdf,.doc,.txt",
    )
    parser.add_argument(
        "--exclude-ext",
        help="Comma-separated extension denylist for file downloads, for example: .gif,.jpg,.exe",
    )
    parser.add_argument(
        "--stay-under-start-path",
        action="store_true",
        help="Only crawl and download URLs whose path stays under the start URL path.",
    )
    parser.add_argument("--dry-run", action="store_true", help="List downloads without writing downloaded files.")
    parser.add_argument(
        "--user-agent",
        default="ChaosToolboxResearchDownloader/0.1 (+local academic archive; respectful crawl)",
        help="User-Agent string.",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    include_extensions = parse_extension_list(args.include_ext)
    exclude_extensions = parse_extension_list(args.exclude_ext)

    if args.download_assets_from_manifest:
        if args.dry_run:
            raise SystemExit("--dry-run is not supported with --download-assets-from-manifest")
        records = download_assets_from_manifest(
            output_dir,
            max_files=args.max_files,
            delay=args.delay,
            timeout=args.timeout,
            user_agent=args.user_agent,
            overwrite=args.overwrite,
            include_extensions=include_extensions,
            exclude_extensions=exclude_extensions,
            download_unknown=args.download_unknown,
        )
    else:
        records = crawl(
            args.start,
            output_dir,
            max_pages=args.max_pages,
            max_files=args.max_files,
            delay=args.delay,
            timeout=args.timeout,
            user_agent=args.user_agent,
            save_pages=args.save_pages,
            overwrite=args.overwrite,
            download_unknown=args.download_unknown,
            include_extensions=include_extensions,
            exclude_extensions=exclude_extensions,
            stay_under_start_path=args.stay_under_start_path,
            dry_run=args.dry_run,
        )

    downloaded = sum(1 for record in records if record.status == "downloaded")
    page_saved = sum(1 for record in records if record.status == "page_saved")
    skipped = sum(1 for record in records if record.status == "skipped_exists")
    errors = sum(1 for record in records if "error" in record.status)

    print()
    print("Done.")
    print(f"Downloaded: {downloaded}")
    print(f"Pages saved: {page_saved}")
    print(f"Skipped existing: {skipped}")
    print(f"Errors: {errors}")
    print(f"Manifest: {output_dir / 'manifest.csv'}")
    print(f"Manifest JSONL: {output_dir / 'manifest.jsonl'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
