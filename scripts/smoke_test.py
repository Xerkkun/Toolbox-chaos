from __future__ import annotations

from pathlib import Path
import os
import sys
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from core.qt_binding import configure_pyside6

configure_pyside6()

from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QLabel
import matplotlib
import numpy as np
import pyqtgraph

from core.native import library
from core.lorenz import simulate_system, system_defaults
from core.sprott import decode_code, multi_indices
from core.sprott.catalog import load_synthetic_examples
from tools.generate_sprott_example_thumbnails import render_example_thumbnail
from ui.sprott_explorer_tab import SprottExplorerTab


# ── Helper ────────────────────────────────────────────────────────────────────

def _check(condition: bool, msg: str) -> None:
    if not condition:
        raise RuntimeError(msg)


def main() -> int:
    _ = (matplotlib, np, pyqtgraph, QtCore)

    # ── 1. Native library ─────────────────────────────────────────────────────
    library()

    # ── 2. Lorenz simulation ──────────────────────────────────────────────────
    params, initial = system_defaults('lorenz')
    t, states = simulate_system('lorenz', initial, params, dt=0.01, T=0.1, method_key='rk4')
    _check(t.shape[0] >= 2 and states.shape == (t.shape[0], 3),
           f'Unexpected Lorenz output shapes: t={t.shape}, states={states.shape}')
    _check(np.all(np.isfinite(states)),
           'Lorenz smoke simulation returned non-finite values.')

    # ── 3. Required assets & PDF Content Verification ────────────────────────
    import pypdf
    
    dictionary = REPO_ROOT / 'assets' / 'chaos_dictionary.pdf'
    _check(dictionary.exists(), f'Required educational asset is missing: {dictionary}')
    
    # Verify chaos_dictionary.pdf content
    dict_reader = pypdf.PdfReader(dictionary)
    _check(len(dict_reader.pages) > 0, "chaos_dictionary.pdf has 0 pages.")
    dict_text = "".join(page.extract_text() or "" for page in dict_reader.pages)
    _check("Diccionario" in dict_text, 
           "chaos_dictionary.pdf is missing dictionary title.")
    _check("Lorenz" in dict_text, 
           "chaos_dictionary.pdf is missing system content.")
    _check("Unified Lorenz" in dict_text,
           "chaos_dictionary.pdf is missing Unified Lorenz-Chen.")
    _check("Sprott S" in dict_text,
           "chaos_dictionary.pdf is missing Sprott S.")
    print("chaos_dictionary.pdf content OK")

    theory_pdf = REPO_ROOT / 'assets' / 'sprott' / 'sprott_theory.pdf'
    _check(theory_pdf.exists(), f'Required educational asset is missing: {theory_pdf}')
    
    # Verify sprott_theory.pdf content
    theory_reader = pypdf.PdfReader(theory_pdf)
    theory_text = "".join(page.extract_text() or "" for page in theory_reader.pages)
    _check("del Explorador Sprott" in theory_text, 
           "sprott_theory.pdf is missing Sprott theory title.")
    _check("Catálogo de sistemas del libro de Wang" not in theory_text, 
           "sprott_theory.pdf erroneously contains Wang catalog content.")
    _check("Wang, Kuznetsov y Chen" not in theory_text, 
           "sprott_theory.pdf erroneously contains Wang catalog authors.")
    print("sprott_theory.pdf content OK")
    
    # Verify sprott_theory.tex source file does not contain wang_systems
    theory_tex_path = REPO_ROOT / 'assets' / 'sprott' / 'sprott_theory.tex'
    _check(theory_tex_path.exists(), f"Source file missing: {theory_tex_path}")
    theory_tex = theory_tex_path.read_text(encoding='utf-8')
    _check("wang_systems" not in theory_tex, 
           "sprott_theory.tex still contains input or reference to wang_systems.")
    print("sprott_theory.tex source file content OK")

    # ── 4. QtPdf availability ─────────────────────────────────────────────────
    try:
        from PySide6.QtPdf import QPdfDocument        # noqa: F401
        from PySide6.QtPdfWidgets import QPdfView     # noqa: F401
        print('QtPdf OK: embedded PDF viewer will be available')
    except ImportError as exc:
        print(f'WARNING: QtPdf not available ({exc}) — PDF viewer will fall back to HTML/text')

    # ── 5. Sprott codec ───────────────────────────────────────────────────────
    code = decode_code('AWMA')
    _check(code.family_letter == 'A' and code.dimension == 1 and code.order == 2,
           f'Unexpected Sprott decode result: {code}')
    _check(len(multi_indices(2, 2)) == 6,
           'Unexpected Sprott monomial count for D=2, O=2.')

    # ── 6. Synthetic examples ─────────────────────────────────────────────────
    examples = load_synthetic_examples()
    _check(len(examples) >= 10, 'Sprott synthetic examples did not load.')
    _check(all(item.get('learning_goal') and item.get('visual_intent') for item in examples),
           'Sprott synthetic examples must include learning_goal and visual_intent.')

    # ── 7. Thumbnail rendering ────────────────────────────────────────────────
    app = QApplication.instance() or QApplication([])
    first_visual = next(
        (item for item in examples if item.get('starter_label') == 'Primera imagen bonita'),
        examples[0],
    )
    with TemporaryDirectory(prefix='chaos-toolbox-smoke-') as temporary_dir:
        thumb = render_example_thumbnail(
            first_visual, Path(temporary_dir) / 'smoke_thumb.png', app=app
        )
        _check(thumb.exists() and thumb.stat().st_size >= 1000,
               'Sprott example thumbnail smoke render failed.')

    # ── 8. SprottExplorerTab construction ─────────────────────────────────────
    tab = SprottExplorerTab()

    # ── 8a. Test the three distributed pedagogical manuals ──────────────────
    manual_dir = REPO_ROOT / 'assets' / 'manuals'
    manual_specs = (
        (manual_dir / 'manual_usuario_toolbox_chaos.pdf', 'Usuario'),
        (manual_dir / 'manual_teorico_pedagogico.pdf', 'Teoría'),
        (manual_dir / 'manual_explorador_sprott.pdf', 'Explorador Sprott'),
    )

    for pdf_p, title in manual_specs:
        pdf_widget = tab._make_pdf_viewer(pdf_p, title)
        _check(pdf_widget is not None, f"make_pdf_viewer returned None for {pdf_p}")
        
        # Check that it contains a status label with the diagnostics
        labels = pdf_widget.findChildren(QLabel)
        _check(len(labels) >= 1, f"make_pdf_viewer widget has no QLabel children for {pdf_p}")
        
        # Verify diagnostics label text format
        status_lbl = next((l for l in labels if 'Archivo:' in l.text() and 'QtPdf:' in l.text()), None)
        _check(status_lbl is not None, f"make_pdf_viewer status label not found or has incorrect text format: {[l.text() for l in labels]}")
        print(f"PDF viewer smoke check for {pdf_p.name} OK: {status_lbl.text().replace(chr(0x2502), '|')}")


    # Tab count
    _check(tab.sections.count() == 9,
           f'Unexpected Sprott tab section count: {tab.sections.count()}')

    # Tab order: Tutorial must be 2nd (index 1), Exploración must be 4th (index 3)
    expected_tab_prefixes = {
        0: 'Inicio',
        1: 'Tutorial',
        2: 'Teoria',
        3: 'Codigos',
        4: 'Exploracion',
        5: 'Ejemplos',
        6: 'Galeria',
    }
    for idx, prefix in expected_tab_prefixes.items():
        actual = tab.sections.tabText(idx)
        _check(
            prefix.lower() in actual.lower(),
            f'Tab {idx}: expected prefix "{prefix}", found "{actual}"',
        )

    # No magic numeric tab indices in sprott_explorer_tab.py
    src_path = REPO_ROOT / 'ui' / 'sprott_explorer_tab.py'
    src = src_path.read_text(encoding='utf-8')
    for bad in ('setCurrentIndex(3)', 'setCurrentIndex(6)'):
        _check(bad not in src,
               f'Magic tab index found in sprott_explorer_tab.py: {bad!r}')

    # load_local_dic_examples must use limit=None as default
    _check(
        'def load_local_dic_examples(self, limit=None)' in src,
        'load_local_dic_examples still has a non-None default limit',
    )

    # Action buttons and new widgets must exist on the tab
    for attr in (
        'quick_sim_btn', 'save_gallery_btn', 'dic_status_label',
        'dic_load_limit_combo', 'reading_mode_check',
    ):
        _check(hasattr(tab, attr), f'SprottExplorerTab missing attribute: {attr}')

    # New methods must exist
    for method in (
        'tutorial_apply_preset_and_show', 'load_quick_example_for_preset',
        '_load_bookfigs_full', '_open_book_reading_mode', '_make_pdf_viewer',
    ):
        _check(hasattr(tab, method), f'SprottExplorerTab missing method: {method}')

    # PyInstaller spec must list QtPdf in hiddenimports
    spec_path = REPO_ROOT / 'packaging' / 'pyinstaller' / 'chaos_toolbox.spec'
    if spec_path.exists():
        spec_src = spec_path.read_text(encoding='utf-8')
        _check(
            'PySide6.QtPdf' in spec_src and 'PySide6.QtPdfWidgets' in spec_src,
            'chaos_toolbox.spec is missing PySide6.QtPdf / PySide6.QtPdfWidgets in hiddenimports',
        )
        print('PyInstaller spec: hiddenimports OK')
    else:
        print(f'WARNING: spec file not found at {spec_path}')

    # ── 8b. Verify special families simulation and Z status in search.py ─────
    from core.sprott.search import simulate_candidate
    from core.sprott.codes import explain_support_status
    
    # 1. Simulate family Y (implemented)
    res_special = simulate_candidate("YMMMMMMMMMM", n_iter=100, transient=0)
    _check(res_special["trajectory"].shape == (100, 4), "Special family Y simulation shape mismatch")
    _check("equations" in res_special and "X'" in res_special["equations"], "Special family equations missing or incorrect")
    
    # 2. Check Z is recognized but pending AND/OR validation, and not an error
    status_z = explain_support_status("ZMMMMMMMMMM")
    _check(status_z["support"] == "special_pending", "Z family support status mismatch")
    _check("AND/OR" in status_z["reason"], "Z family pending reason missing AND/OR notice")
    print("Special families simulation & Z status checks: OK")

    # ── 9. Verify no Sprott original files in release paths ──────────────────
    from tools.check_no_sprott_originals_in_release import check_release_cleanliness
    banned_found = check_release_cleanliness()
    _check(len(banned_found) == 0, f"Sprott release check failed: found original files in release paths: {banned_found}")
    print('Sprott release cleanliness check: OK')

    tab.deleteLater()
    app.processEvents()

    print('Smoke test OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
