from __future__ import annotations

from pathlib import Path
import shutil

from core.sprott.references import parse_dic_metrics, read_dic_entries


def test_parse_dic_metrics_named_and_positional():
    assert parse_dic_metrics(['F=2.31', 'L=0.12']) == {'F': 2.31, 'L': 0.12}
    assert parse_dic_metrics(['2.5', '-0.01']) == {'F': 2.5, 'L': -0.01}
    assert parse_dic_metrics(['F', '1.8', 'L', '0.22']) == {'F': 1.8, 'L': 0.22}


def test_read_dic_entries_enriches_support_and_metrics():
    base = Path.cwd() / '.pytest_tmp' / 'sprott_dic_import'
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    try:
        dic = base / 'SAMPLE.DIC'
        dic.write_text('EWMWAMMMPMMMM F=2.4 L=0.1\nYABC F=1.2 L=-0.1\n', encoding='latin-1')
        entries = read_dic_entries(dic)
        assert entries[0]['support'] == 'simulable'
        assert entries[0]['kind'] == 'map'
        assert entries[0]['dimension'] == 2
        assert entries[0]['f_metric'] == 2.4
        assert entries[0]['l_metric'] == 0.1
        assert entries[1]['support'] == 'familia especial pendiente'
    finally:
        if base.exists():
            shutil.rmtree(base)
