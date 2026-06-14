#!/usr/bin/env python3
"""
Locate old tycho.physics.wisc.edu course links on the current web.

The script scans downloaded HTML pages for tycho course URLs, probes likely
current physics.wisc.edu replacements, then queries the Internet Archive CDX API
for archived copies when the live pages are gone.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


TYCHO_URL_RE = re.compile(r"https?://tycho\.physics\.wisc\.edu/[^\s\"'<>]+", re.I)
GENERIC_COURSE_TITLE = "Physics Course Descriptions – Department of Physics – UW–Madison"


@dataclass(frozen=True)
class LocatedUrl:
    source_url: str
    live_candidate: str
    live_status: str
    live_http_status: int | None
    live_content_type: str
    live_title: str
    direct_download: str
    archive_url: str
    archive_timestamp: str
    archive_mimetype: str
    archive_http_status: int | None
    note: str


def extract_tycho_urls(pages_dir: Path) -> list[str]:
    urls: set[str] = set()
    for path in pages_dir.rglob("*"):
        if path.suffix.lower() not in {".htm", ".html"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in TYCHO_URL_RE.finditer(text):
            url = html.unescape(match.group(0)).rstrip(").,;")
            urls.add(url)
    return sorted(urls)


def live_candidate_for(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(
        parsed._replace(scheme="https", netloc="www.physics.wisc.edu")
    )


def open_url(url: str, timeout: float) -> tuple[int | None, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Toolbox-chaos-local-archive/0.1 (+research archive lookup)",
        },
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            content_type = response.headers.get("content-type", "")
            payload = response.read(200_000)
            return response.status, f"{response.url}\n{content_type}", payload
    except urllib.error.HTTPError as exc:
        content_type = exc.headers.get("content-type", "") if exc.headers else ""
        return exc.code, f"{exc.url}\n{content_type}", b""
    except Exception as exc:
        return None, url, str(exc).encode("utf-8", errors="ignore")


def html_title(payload: bytes) -> str:
    text = payload.decode("utf-8", errors="ignore")
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()


def probe_live(url: str, timeout: float) -> tuple[str, int | None, str, str, str]:
    status, response_info, payload = open_url(url, timeout)
    final_url, _, content_type = response_info.partition("\n")
    content_type_lower = content_type.lower()
    path_suffix = Path(urllib.parse.urlparse(final_url).path).suffix.lower()
    direct_download = (
        path_suffix not in {"", ".htm", ".html", ".php", ".asp", ".aspx"}
        or ("text/html" not in content_type_lower and "application/xhtml" not in content_type_lower)
    )
    if status and 200 <= status < 400:
        note = "live_download" if direct_download else "live_html"
        title = html_title(payload) if not direct_download else ""
        return final_url, status, note, content_type, title
    if status is None:
        return "", None, payload.decode("utf-8", errors="ignore")[:160], content_type, ""
    return "", status, "live_missing", content_type, ""


def query_wayback(url: str, timeout: float) -> tuple[str, str, str, int | None]:
    cdx_url = "https://web.archive.org/cdx?" + urllib.parse.urlencode(
        {
            "url": url,
            "output": "json",
            "fl": "timestamp,original,statuscode,mimetype",
            "filter": "statuscode:200",
            "collapse": "digest",
            "limit": "1",
            "sort": "reverse",
        }
    )
    status, _, payload = open_url(cdx_url, timeout)
    if status != 200 or not payload:
        return "", "", "", status

    try:
        rows = json.loads(payload.decode("utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return "", "", "", status

    if len(rows) < 2:
        return "", "", "", status
    timestamp, original, _, mimetype = rows[1]
    archive_url = f"https://web.archive.org/web/{timestamp}/{original}"
    return archive_url, timestamp, mimetype, status


def locate_urls(urls: list[str], timeout: float, delay: float) -> list[LocatedUrl]:
    results: list[LocatedUrl] = []
    for index, source_url in enumerate(urls, start=1):
        live_candidate = live_candidate_for(source_url)
        live_url, live_status, live_note, live_content_type, live_title = probe_live(
            live_candidate, timeout
        )
        time.sleep(delay)

        archive_url = ""
        archive_timestamp = ""
        archive_mimetype = ""
        archive_status: int | None = None
        note = live_note

        live_is_generic = live_title == GENERIC_COURSE_TITLE
        if not live_url or live_is_generic:
            archive_url, archive_timestamp, archive_mimetype, archive_status = query_wayback(
                source_url, timeout
            )
            if archive_url and live_is_generic:
                note = "live_generic_archive_found"
            elif archive_url:
                note = "archive_found"
            else:
                note = f"not_found ({live_note})"
            time.sleep(delay)

        results.append(
            LocatedUrl(
                source_url=source_url,
                live_candidate=live_url or live_candidate,
                live_status="generic_html" if live_is_generic else ("found" if live_url else "missing"),
                live_http_status=live_status,
                live_content_type=live_content_type,
                live_title=live_title,
                direct_download="yes" if live_note == "live_download" else "no",
                archive_url=archive_url,
                archive_timestamp=archive_timestamp,
                archive_mimetype=archive_mimetype,
                archive_http_status=archive_status,
                note=note,
            )
        )
        print(f"[{index}/{len(urls)}] {source_url} -> {note}")
    return results


def write_outputs(results: list[LocatedUrl], archive_dir: Path) -> tuple[Path, Path]:
    csv_path = archive_dir / "tycho_course_lookup.csv"
    md_path = archive_dir / "tycho_course_lookup.md"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(LocatedUrl.__dataclass_fields__))
        writer.writeheader()
        for result in results:
            writer.writerow(result.__dict__)

    live_count = sum(1 for result in results if result.live_status == "found")
    direct_downloads = sum(1 for result in results if result.direct_download == "yes")
    generic_course_pages = sum(1 for result in results if result.live_status == "generic_html")
    archived_count = sum(1 for result in results if result.archive_url)
    missing_count = len(results) - live_count - archived_count
    lines = [
        "# Tycho course link lookup",
        "",
        f"- Source links checked: {len(results)}",
        f"- Live www.physics.wisc.edu links found: {live_count}",
        f"- Direct downloadable live links: {direct_downloads}",
        f"- Live links returning the modern course-description page: {generic_course_pages}",
        f"- Internet Archive links found: {archived_count}",
        f"- Not found: {missing_count}",
        "",
        "| Original | Live candidate/status | Content | Archive | Note |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        live = result.live_candidate
        if result.live_status == "found":
            live = f"[live]({result.live_candidate})"
        archive = (
            f"[{result.archive_timestamp}]({result.archive_url})"
            if result.archive_url
            else ""
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"[original]({result.source_url})",
                    live,
                    f"{result.live_content_type or ''}<br>{result.live_title or ''}<br>direct_download={result.direct_download}",
                    archive,
                    result.note.replace("|", "/"),
                ]
            )
            + " |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find archived Tycho course URLs.")
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("external/sprott_site_theory"),
        help="Archive directory containing pages/.",
    )
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--delay", type=float, default=0.4)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive_dir = args.archive.resolve()
    urls = extract_tycho_urls(archive_dir / "pages")
    if not urls:
        print("No tycho.physics.wisc.edu URLs found.")
        return 0

    results = locate_urls(urls, args.timeout, args.delay)
    csv_path, md_path = write_outputs(results, archive_dir)
    print(f"CSV: {csv_path}")
    print(f"Report: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
