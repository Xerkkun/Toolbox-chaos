from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import tools.download_sprott_site as downloader


class FakeResponse:
    def __init__(
        self,
        url: str,
        body: bytes,
        *,
        content_length: int | None = None,
        chunk_size: int = 3,
        interrupt_after_reads: int | None = None,
    ) -> None:
        self.url = url
        self.body = body
        self.offset = 0
        self.chunk_size = chunk_size
        self.interrupt_after_reads = interrupt_after_reads
        self.read_sizes: list[int] = []
        self.status = 200
        self.closed = False
        self.headers = {'Content-Type': 'application/octet-stream'}
        if content_length is not None:
            self.headers['Content-Length'] = str(content_length)

    def __enter__(self) -> 'FakeResponse':
        return self

    def __exit__(self, *_args: object) -> None:
        self.closed = True

    def geturl(self) -> str:
        return self.url

    def read(self, size: int) -> bytes:
        if (
            self.interrupt_after_reads is not None
            and len(self.read_sizes) >= self.interrupt_after_reads
        ):
            raise KeyboardInterrupt
        self.read_sizes.append(size)
        if self.offset >= len(self.body):
            return b''
        amount = min(size, self.chunk_size, len(self.body) - self.offset)
        chunk = self.body[self.offset:self.offset + amount]
        self.offset += amount
        return chunk


class QueueOpener:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.opened_urls: list[str] = []

    def open(self, request, *, timeout: float):
        del timeout
        self.opened_urls.append(request.full_url)
        if not self.responses:
            raise AssertionError(f'Unexpected request: {request.full_url}')
        return self.responses.pop(0)


def _install_opener(monkeypatch, *responses: FakeResponse) -> QueueOpener:
    opener = QueueOpener(list(responses))
    monkeypatch.setattr(
        downloader.urllib.request,
        'build_opener',
        lambda *_handlers: opener,
    )
    return opener


def _page_record(output_dir: Path, html: str) -> downloader.DownloadRecord:
    pages = output_dir / 'pages'
    pages.mkdir(parents=True, exist_ok=True)
    page = pages / 'index.html'
    page.write_text(html, encoding='utf-8')
    return downloader.DownloadRecord(
        'https://sprott.physics.wisc.edu/index.html',
        str(page),
        'page_saved',
        200,
        'text/html',
        page.stat().st_size,
        hashlib.sha256(page.read_bytes()).hexdigest(),
        None,
    )


def test_robots_failure_is_fail_closed(monkeypatch):
    def fail_request(*_args, **_kwargs):
        raise OSError('network unavailable')

    monkeypatch.setattr(downloader, 'open_request', fail_request)
    with pytest.raises(
        downloader.RobotsPolicyError,
        match='robots.txt.*fail-closed',
    ):
        downloader.load_robots(
            downloader.DEFAULT_START_URL,
            user_agent='test-agent',
            timeout=1.0,
            allowed_netloc='sprott.physics.wisc.edu',
        )


def test_download_streams_chunks_and_enforces_actual_limit(tmp_path, monkeypatch):
    url = 'https://sprott.physics.wisc.edu/archive.bin'
    response = FakeResponse(url, b'abcdefghij', content_length=10, chunk_size=3)
    _install_opener(monkeypatch, response)

    record = downloader.download_file(
        url,
        tmp_path,
        'test-agent',
        1.0,
        False,
        max_bytes=16,
    )

    assert record.status == 'downloaded'
    assert Path(record.local_path).read_bytes() == b'abcdefghij'
    assert record.sha256 == hashlib.sha256(b'abcdefghij').hexdigest()
    assert len(response.read_sizes) >= 4
    assert max(response.read_sizes) <= downloader.STREAM_CHUNK_BYTES

    oversized_url = 'https://sprott.physics.wisc.edu/oversized.bin'
    oversized = FakeResponse(oversized_url, b'12345', chunk_size=2)
    _install_opener(monkeypatch, oversized)
    rejected = downloader.download_file(
        oversized_url,
        tmp_path,
        'test-agent',
        1.0,
        False,
        max_bytes=4,
    )
    assert rejected.status == 'error'
    assert 'límite de 4 bytes' in (rejected.error or '')
    assert not Path(rejected.local_path).exists()
    assert not list(tmp_path.rglob('*.tmp'))


def test_aggregate_budget_stops_second_response_and_checkpoints(
    tmp_path, monkeypatch
):
    page = _page_record(
        tmp_path,
        '<a href="/a.bin">a</a><a href="/b.bin">b</a>',
    )
    downloader.write_manifest(tmp_path, [page])
    first_url = 'https://sprott.physics.wisc.edu/a.bin'
    second_url = 'https://sprott.physics.wisc.edu/b.bin'
    first = FakeResponse(first_url, b'123456', chunk_size=2)
    second = FakeResponse(second_url, b'abcdef', chunk_size=2)
    opener = _install_opener(monkeypatch, first, second)

    with pytest.raises(downloader.DownloadBudgetExceeded, match='presupuesto agregado'):
        downloader.download_assets_from_manifest(
            tmp_path,
            max_files=2,
            delay=0.0,
            timeout=1.0,
            user_agent='test-agent',
            overwrite=False,
            include_extensions={'.bin'},
            exclude_extensions=None,
            download_unknown=False,
            max_file_bytes=64,
            max_total_bytes=page.size_bytes + 10,
            manifest_checkpoint_every=20,
        )

    first_path = downloader.safe_local_path(tmp_path, first_url, 'files')
    second_path = downloader.safe_local_path(tmp_path, second_url, 'files')
    assert first_path.read_bytes() == b'123456'
    assert not second_path.exists()
    assert opener.opened_urls == [first_url, second_url]
    assert not list(tmp_path.rglob('*.tmp'))
    resumed = {record.url: record for record in downloader.load_manifest(tmp_path)}
    assert resumed[first_url].status == 'downloaded'
    assert second_url not in resumed


def test_aggregate_budget_counts_existing_files_and_manifest(
    tmp_path, monkeypatch
):
    page = _page_record(tmp_path, '<a href="/new.bin">new</a>')
    orphan_url = 'https://sprott.physics.wisc.edu/orphan.bin'
    orphan_path = downloader.safe_local_path(tmp_path, orphan_url, 'files')
    orphan_path.write_bytes(b'12345678')
    reserved_url = 'https://sprott.physics.wisc.edu/reserved.bin'
    reserved_path = downloader.safe_local_path(tmp_path, reserved_url, 'files')
    reserved = downloader.DownloadRecord(
        reserved_url,
        str(reserved_path),
        'downloaded',
        200,
        'application/octet-stream',
        2,
        None,
        None,
    )
    downloader.write_manifest(tmp_path, [page, reserved])

    new_url = 'https://sprott.physics.wisc.edu/new.bin'
    response = FakeResponse(new_url, b'abcd', content_length=4)
    opener = _install_opener(monkeypatch, response)
    with pytest.raises(downloader.DownloadBudgetExceeded, match='restante'):
        downloader.download_assets_from_manifest(
            tmp_path,
            max_files=1,
            delay=0.0,
            timeout=1.0,
            user_agent='test-agent',
            overwrite=False,
            include_extensions={'.bin'},
            exclude_extensions=None,
            download_unknown=False,
            max_file_bytes=64,
            max_total_bytes=page.size_bytes + 12,
        )

    assert opener.opened_urls == [new_url]
    assert response.read_sizes == []
    assert orphan_path.read_bytes() == b'12345678'
    assert not downloader.safe_local_path(tmp_path, new_url, 'files').exists()


def test_interrupted_stream_removes_temporary_file(tmp_path, monkeypatch):
    url = 'https://sprott.physics.wisc.edu/interrupted.bin'
    response = FakeResponse(
        url,
        b'abcdef',
        chunk_size=2,
        interrupt_after_reads=1,
    )
    _install_opener(monkeypatch, response)

    with pytest.raises(KeyboardInterrupt):
        downloader.download_file(
            url,
            tmp_path,
            'test-agent',
            1.0,
            False,
            max_bytes=16,
        )

    assert not downloader.safe_local_path(tmp_path, url, 'files').exists()
    assert not list(tmp_path.rglob('*.tmp'))


def test_manifest_interruption_preserves_published_files(tmp_path, monkeypatch):
    initial = [
        downloader.DownloadRecord(
            'https://sprott.physics.wisc.edu/old.bin',
            '',
            'downloaded',
            200,
            'application/octet-stream',
            3,
            'old-hash',
            None,
        )
    ]
    downloader.write_manifest(tmp_path, initial)
    old_csv = (tmp_path / 'manifest.csv').read_bytes()
    old_jsonl = (tmp_path / 'manifest.jsonl').read_bytes()

    def interrupt_json(*_args, **_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(downloader.json, 'dumps', interrupt_json)
    with pytest.raises(KeyboardInterrupt):
        downloader.write_manifest(
            tmp_path,
            initial
            + [
                downloader.DownloadRecord(
                    'https://sprott.physics.wisc.edu/new.bin',
                    '',
                    'downloaded',
                    200,
                    'application/octet-stream',
                    3,
                    'new-hash',
                    None,
                )
            ],
        )

    assert (tmp_path / 'manifest.csv').read_bytes() == old_csv
    assert (tmp_path / 'manifest.jsonl').read_bytes() == old_jsonl
    assert not list(tmp_path.rglob('*.tmp'))


def test_manifest_checkpoint_batches_writes(tmp_path, monkeypatch):
    records: list[downloader.DownloadRecord] = []
    snapshots: list[int] = []
    monkeypatch.setattr(
        downloader,
        'write_manifest',
        lambda _output, current: snapshots.append(len(current)),
    )
    checkpoint = downloader.ManifestCheckpoint(
        tmp_path,
        lambda: list(records),
        every=3,
    )
    for index in range(7):
        records.append(
            downloader.DownloadRecord(
                f'https://sprott.physics.wisc.edu/{index}.bin',
                '',
                'downloaded',
                200,
                'application/octet-stream',
                1,
                None,
                None,
            )
        )
        checkpoint.changed()
    checkpoint.flush(force=True)

    assert snapshots == [3, 6, 7]


def test_cli_reports_budget_abort_without_traceback(tmp_path, monkeypatch, capsys):
    def abort(*_args, **_kwargs):
        raise downloader.DownloadBudgetExceeded('budget exhausted')

    monkeypatch.setattr(downloader, 'download_assets_from_manifest', abort)
    result = downloader.main(
        [
            '--output',
            str(tmp_path),
            '--download-assets-from-manifest',
        ]
    )
    captured = capsys.readouterr()
    assert result == 2
    assert 'budget exhausted' in captured.err
