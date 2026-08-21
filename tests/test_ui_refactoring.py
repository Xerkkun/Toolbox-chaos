from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication, QPushButton

# Setup QApplication offscreen for testing
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
_app = QApplication.instance() or QApplication([])

from ui.main_window import MainWindow
import ui.sprott_explorer_tab as sprott_explorer_module
from ui.tab_controls import (
    Tab3DWidget,
    Tab2DWidget,
    TabTimeSeriesWidget,
    TabFFTWidget,
    TabBifurcationWidget,
    TabBasinWidget,
    TabLyapunovWidget,
    TabSpectrumWidget,
    TabComparisonWidget,
    TabCoexistenceWidget,
    bifurcation_capability,
)
from core.lorenz import METHOD_REGISTRY, SYSTEM_REGISTRY
from ui.canvases import BASIN_RESIDUAL_LABEL, MplBasinCanvas
from ui.parameter_panels import SystemParameterPanel
from core.coexistence import load_coexisting_attractors
from core.sprott.metrics import LyapunovEstimate
from core.sprott.references import classify_dic_entry


def test_mainwindow_construction():
    """Verify that MainWindow can be constructed and has all required tabs."""
    window = MainWindow()
    assert window is not None
    assert window.tabs.count() >= 12

    # Check that the Coexistence tab is present
    found_coex = False
    for i in range(window.tabs.count()):
        if 'coexistencia' in window.tabs.tabText(i).lower():
            found_coex = True
            break
    assert found_coex, "Coexistence tab not found in MainWindow tabs"
    assert any(
        'crear sistema' in window.tabs.tabText(i).lower()
        for i in range(window.tabs.count())
    ), "No-code system editor tab not found"
    assert hasattr(window, 'tab_custom_system')
    window.deleteLater()


def test_sprott_home_has_three_guided_routes():
    window = MainWindow()
    explorer = window.tab_sprott
    labels = {button.text() for button in explorer.findChildren(QPushButton)}
    assert '1. Probar ejemplo' in labels
    assert '2. Decodificar codigo' in labels
    assert '3. Abrir archivo .DIC' in labels

    explorer.start_guided_example()
    assert 'explor' in explorer.sections.tabText(explorer.sections.currentIndex()).lower()
    assert explorer.last_result is not None
    explorer.open_code_decoder()
    assert 'codigo' in explorer.sections.tabText(explorer.sections.currentIndex()).lower()
    window.deleteLater()


def test_tab_save_buttons():
    """Verify that each simulation/plotting tab contains a save button."""
    window = MainWindow()

    widgets_to_check = [
        window.tab_3d_widget,
        window.tab_2d_widget,
        window.tab_time_widget,
        window.tab_fft_widget,
        window.tab_lyap_widget,
        window.tab_bif_widget,
        window.tab_basin_widget,
        window.tab_spectrum_widget,
        window.tab_method_compare_widget,
        window.tab_coexistence_widget,
    ]

    for widget in widgets_to_check:
        buttons = widget.findChildren(QPushButton)
        save_btn = next(
            (btn for btn in buttons if 'guardar' in btn.text().lower()), None
        )
        assert (
            save_btn is not None
        ), f"Save button not found in tab {widget.__class__.__name__}"

    window.deleteLater()


def test_fft_calculation_button():
    """Verify FFT tab has its calculation button inside the tab."""
    tab = TabFFTWidget()
    buttons = tab.findChildren(QPushButton)
    calc_btn = next(
        (btn for btn in buttons if 'calcular fft' in btn.text().lower()), None
    )
    assert calc_btn is not None, "Calculation button not found in FFT tab"
    tab.deleteLater()


def test_bifurcation_calculation_button():
    """Verify Bifurcation tab has its calculation button inside the tab."""
    tab = TabBifurcationWidget()
    buttons = tab.findChildren(QPushButton)
    calc_btn = next(
        (btn for btn in buttons if 'calcular bifurcaci' in btn.text().lower()),
        None,
    )
    assert (
        calc_btn is not None
    ), "Calculation button not found in Bifurcation tab"
    tab.deleteLater()


@pytest.mark.parametrize(
    'system_key', [f'sprott_{letter}' for letter in 'abcdefghijklmnopqrs']
)
def test_parameterless_sprott_flows_disable_bifurcation(system_key):
    metadata = SYSTEM_REGISTRY[system_key]
    supported, reason = bifurcation_capability(metadata)
    assert supported is False
    assert 'parámetro' in reason.lower()

    tab = TabBifurcationWidget()
    tab._update_bifurcation_defaults(system_key)
    assert tab.sweep_param_combo.count() == 0
    assert not tab.btn_run.isEnabled()
    assert 'parámetro' in tab.lbl_warning.text().lower()
    tab.deleteLater()


@pytest.mark.parametrize('system_key', ['lorenz', 'mackey_glass', 'lorenz96'])
def test_parameterized_systems_keep_valid_bifurcation_capability(system_key):
    supported, reason = bifurcation_capability(SYSTEM_REGISTRY[system_key])
    assert supported is True
    assert reason == ''


def test_basin_calculation_button():
    """Verify Basin tab has its calculation button inside the tab."""
    tab = TabBasinWidget()
    buttons = tab.findChildren(QPushButton)
    calc_btn = next(
        (btn for btn in buttons if 'calcular cuenca' in btn.text().lower()),
        None,
    )
    assert calc_btn is not None, "Calculation button not found in Basin tab"
    tab.deleteLater()


def test_default_basin_class_one_is_residual_not_chaos():
    canvas = MplBasinCanvas()
    canvas.plot_basin(
        np.array([[0, 1]], dtype=float),
        (0.0, 1.0, 0.0, 1.0),
        0.0,
        0.0,
    )
    legend = canvas.ax.get_legend()
    assert legend is not None
    assert BASIN_RESIDUAL_LABEL in [item.get_text() for item in legend.get_texts()]
    canvas.deleteLater()


@pytest.mark.parametrize('system_key', ['lorenz', 'rossler'])
def test_basin_tab_uses_residual_label_for_system_specific_legends(
    monkeypatch, system_key
):
    tab = TabBasinWidget()
    system_index = tab.param_panel.system_combo.findData(system_key)
    tab.param_panel.system_combo.setCurrentIndex(system_index)
    tab.last_basin = np.array([[1]], dtype=float)
    tab.last_basin_extent = (0.0, 1.0, 0.0, 1.0)
    tab.last_basin_rho = 0.0
    tab.last_basin_z0 = 0.0
    tab.last_equilibria = []
    captured = {}
    monkeypatch.setattr(
        tab.canvas,
        'plot_basin',
        lambda *_args, **kwargs: captured.update(kwargs),
    )
    tab._refresh_canvas()
    assert captured['class_labels'][1] == BASIN_RESIDUAL_LABEL
    tab.deleteLater()


def test_dictionary_matches_basin_and_current_spectral_contracts():
    text = (
        Path(__file__).resolve().parents[1] / 'assets' / 'chaos_dictionary.tex'
    ).read_text(encoding='utf-8')
    assert 'Acotado residual / no clasificado' in text
    assert '\\textbf{Caotico}' not in text
    assert 'PSD de Welch y espectro de amplitud' in text
    assert 'U^2/\\mathrm{Hz}' in text
    assert 'sin \\texttt{fftshift} ni frecuencias negativas' in text


def test_pedagogical_manuals_are_integrated_as_distinct_documents():
    root = Path(__file__).resolve().parents[1]
    filenames = {
        'manual_usuario_toolbox_chaos.pdf',
        'manual_teorico_pedagogico.pdf',
        'manual_explorador_sprott.pdf',
    }
    for filename in filenames:
        assert (root / 'assets' / 'manuals' / filename).is_file()

    metadata = (root / 'core' / 'app_metadata.py').read_text(encoding='utf-8')
    main_window = (root / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    sprott = (root / 'ui' / 'sprott_explorer_tab.py').read_text(encoding='utf-8')
    assert 'manual_usuario_toolbox_chaos.pdf' in metadata
    assert "self.tabs.addTab(self.tab_dict, 'Manuales')" in main_window
    assert filenames.issubset(set(main_window.split("'")))
    assert "bundled_doc_path('manual_teorico_pedagogico.pdf')" in sprott
    assert "bundled_doc_path('manual_explorador_sprott.pdf')" in sprott


def test_no_global_sidebar():
    """Verify there is no global sidebar or controls layout in the main window."""
    window = MainWindow()
    # Central widget is parent layout of QTabWidget and info_label
    # No global controls_scroll should be in MainWindow central widget or MainWindow layout
    assert not hasattr(window, 'controls_scroll')
    window.deleteLater()


def test_parameter_panel_system_change():
    """Verify that changing system in parameter panel updates dynamic parameters."""
    window = MainWindow()
    panel = window.tab_3d_widget.param_panel

    # Switch to Rossler (a, b, c)
    panel.system_combo.setCurrentIndex(panel.system_combo.findData('rossler'))
    assert panel.param_labels[0].text() == 'a'
    assert panel.param_labels[1].text() == 'b'
    assert panel.param_labels[2].text() == 'c'
    assert not panel.param_labels[3].isVisible()

    # Switch to Lorenz (sigma, rho, beta)
    panel.system_combo.setCurrentIndex(panel.system_combo.findData('lorenz'))
    assert panel.param_labels[0].text() == 'sigma'
    assert panel.param_labels[1].text() == 'rho'
    assert panel.param_labels[2].text() == 'beta'
    assert not panel.param_labels[3].isVisible()

    window.deleteLater()


def test_parameter_panel_disables_planned_methods_but_keeps_dde_methods_active():
    panel = SystemParameterPanel()
    model = panel.method_combo.model()
    for key, metadata in METHOD_REGISTRY.items():
        index = panel.method_combo.findData(key)
        assert index >= 0
        item = model.item(index)
        assert item is not None
        assert item.isEnabled() is bool(metadata['implemented'])

    panel.system_combo.setCurrentIndex(
        panel.system_combo.findData('mackey_glass')
    )
    assert panel.method_combo.isEnabled()
    panel.deleteLater()


def test_sprott_explorer_exposes_real_unit_sphere_projection():
    window = MainWindow()
    explorer = window.tab_sprott
    index = explorer.projection_combo.findText('esfera unitaria')
    assert index >= 0
    explorer.projection_combo.setCurrentIndex(index)
    assert explorer.current_visual_config().projection == 'esfera unitaria'
    assert explorer.projection_combo.findText('esfera (pendiente)') == -1
    window.deleteLater()


def test_lyapunov_tab_exposes_fixed_rk4_without_editable_method_selector():
    tab = TabLyapunovWidget()
    assert not hasattr(tab.param_panel, 'method_combo')
    assert 'RK4 fijo' in tab.integrator_label.text()
    tab.deleteLater()


def test_sprott_z_is_reference_only_while_y_remains_operational():
    window = MainWindow()
    explorer = window.tab_sprott
    y_entry = {
        'code': 'Y' + 'M' * 10, 'source_name': 'test.dic', 'line': 1,
        **classify_dic_entry('Y' + 'M' * 10),
    }
    z_entry = {
        'code': 'Z' + 'M' * 10, 'source_name': 'test.dic', 'line': 2,
        **classify_dic_entry('Z' + 'M' * 10),
    }
    explorer.local_dic_visible_entries = [y_entry, z_entry]
    explorer.show_selected_local_dic(0)
    assert explorer.local_dic_sim_button.isEnabled()
    assert explorer.local_dic_style_button.isEnabled()
    explorer.show_selected_local_dic(1)
    assert not explorer.local_dic_sim_button.isEnabled()
    assert not explorer.local_dic_style_button.isEnabled()
    assert 'No simulable' in explorer.local_dic_sim_button.toolTip()
    window.deleteLater()


def test_sprott_search_attempt_preserves_structured_lyapunov_context(monkeypatch):
    window = MainWindow()
    explorer = window.tab_sprott
    trajectory = np.column_stack((
        np.linspace(0.0, 1.0, 80), np.linspace(1.0, 2.0, 80)
    ))
    result = {'post_transient': trajectory}
    classification = {'state': 'candidate_chaotic', 'reason': 'test'}
    monkeypatch.setattr(
        sprott_explorer_module,
        'quick_lyapunov_estimate',
        lambda *_args, **_kwargs: LyapunovEstimate(0.125, 'ok', []),
    )
    explorer._record_search_attempt(1, 'EMMMM', result, classification)
    assert explorer.search_attempts[-1]['lyapunov'] == '0.125'

    monkeypatch.setattr(
        sprott_explorer_module,
        'quick_lyapunov_estimate',
        lambda *_args, **_kwargs: LyapunovEstimate(
            float('nan'), 'not_available_special_family', ['index dependent']
        ),
    )
    explorer._record_search_attempt(2, 'YMMMM', result, classification)
    text = explorer.search_attempts[-1]['lyapunov']
    assert 'not_available_special_family' in text
    assert 'index dependent' in text

    def fail(*_args, **_kwargs):
        raise RuntimeError('diagnostic failed')

    monkeypatch.setattr(sprott_explorer_module, 'quick_lyapunov_estimate', fail)
    explorer._record_search_attempt(3, 'EMMMM', result, classification)
    assert 'diagnostic failed' in explorer.search_attempts[-1]['lyapunov']
    window.deleteLater()


def test_reproducible_examples_use_each_tabs_parameter_panel():
    text = (
        Path(__file__).resolve().parents[1] / 'docs' / 'reproducible-examples.md'
    ).read_text(encoding='utf-8')
    assert 'left sidebar' not in text.lower()
    for tab_name in ('Atractor 3D', 'Lyapunov', 'Bifurcación', 'Cuenca de atracción'):
        assert f'Open the **{tab_name}** tab.' in text
    assert text.count('In the left parameter panel of that tab') == 5


def test_coexistence_yaml_loading():
    """Verify data/coexisting_attractors.yaml contains valid metadata and references."""
    cases = load_coexisting_attractors()
    assert len(cases) > 0

    for case in cases:
        sys_key = case.get('system_key')
        assert (
            sys_key in SYSTEM_REGISTRY
        ), f"System key {sys_key} in coexistence YAML is not present in SYSTEM_REGISTRY"

        # Check initial condition dimension (usually 3D for flow systems)
        attractors = case.get('attractors', [])
        assert len(attractors) >= 2, "Each case must have at least 2 attractors"
        for attr in attractors:
            ic = attr.get('initial_condition', [])
            assert (
                len(ic) == 3
            ), f"Initial condition {ic} must have exactly 3 coordinates"


def test_high_dimension_widgets():
    """Verify that selecting a 4D system updates Tab3DWidget, Tab2DWidget, TabTimeSeriesWidget, and SystemParameterPanel correctly."""
    window = MainWindow()

    # Get the tabs
    tab3d = window.tab_3d_widget
    tab2d = window.tab_2d_widget
    tabtime = window.tab_time_widget

    # Set system to hyper_lorenz (4D) in 3D tab
    tab3d.param_panel.system_combo.setCurrentIndex(
        tab3d.param_panel.system_combo.findData('hyper_lorenz')
    )
    # Check 3D widget is disabled
    assert tab3d.stacked_widget.currentIndex() == 1
    assert not tab3d.btn_run.isEnabled()
    assert not tab3d.btn_save.isEnabled()
    
    # Check 4 initial conditions in SystemParameterPanel
    assert not tab3d.param_panel.ic_spins[0].isHidden()
    assert not tab3d.param_panel.ic_spins[3].isHidden()
    assert tab3d.param_panel.ic_spins[4].isHidden()

    # Set system to hyper_lorenz in 2D tab
    tab2d.param_panel.system_combo.setCurrentIndex(
        tab2d.param_panel.system_combo.findData('hyper_lorenz')
    )
    # 4D system has 6 pairwise combinations (4 choose 2)
    assert len(tab2d.checkboxes) == 6
    assert len(tab2d.plot_widgets) == 6

    # Set system to hyper_lorenz in Time Series tab
    tabtime.param_panel.system_combo.setCurrentIndex(
        tabtime.param_panel.system_combo.findData('hyper_lorenz')
    )
    # 4D system has 4 time series plots
    assert len(tabtime.plot_widgets) == 4
    assert len(tabtime.color_combos) == 4

    window.deleteLater()


def test_bifurcation_widget_run_no_coex(monkeypatch):
    """Verify TabBifurcationWidget runs bifurcation calculation correctly for system without coexistence."""
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, 'critical', lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, 'information', lambda *args, **kwargs: None)

    tab = TabBifurcationWidget()
    # Switch system to Rossler (no coexistence)
    tab.param_panel.system_combo.setCurrentIndex(tab.param_panel.system_combo.findData('rossler'))
    
    # Verify chk_compare is disabled and unchecked
    assert not tab.chk_compare.isEnabled()
    assert not tab.chk_compare.isChecked()
    
    # Run bifurcation sweep
    tab.run_bifurcation()
    
    # Warning label should not indicate an error
    assert not tab.lbl_warning.text().startswith("Error:")
    tab.deleteLater()


def test_bifurcation_widget_run_with_coex(monkeypatch):
    """Verify TabBifurcationWidget runs bifurcation calculation correctly for system with coexistence."""
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, 'critical', lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, 'information', lambda *args, **kwargs: None)

    tab = TabBifurcationWidget()
    # Switch system to Lorenz (has coexistence)
    tab.param_panel.system_combo.setCurrentIndex(tab.param_panel.system_combo.findData('lorenz'))
    
    # Verify chk_compare is enabled
    assert tab.chk_compare.isEnabled()
    
    # Case 1: single sweep (compare unchecked)
    tab.chk_compare.setChecked(False)
    tab.run_bifurcation()
    assert not tab.lbl_warning.text().startswith("Error:")
    
    # Case 2: dual sweep (compare checked)
    tab.chk_compare.setChecked(True)
    tab.run_bifurcation()
    assert not tab.lbl_warning.text().startswith("Error:")
    
    tab.deleteLater()


def test_coexistence_widget_simulations(monkeypatch):
    """Verify TabCoexistenceWidget loads cases and runs simulations correctly."""
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, 'critical', lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, 'information', lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, 'warning', lambda *args, **kwargs: None)

    tab = TabCoexistenceWidget()
    # Ensure cases loaded successfully
    assert len(tab.cases) > 0
    assert tab.case_combo.count() > 0

    # Test simulating one attractor
    tab.case_combo.setCurrentIndex(0)
    tab.simulate_one()

    # Test simulating all attractors
    tab.simulate_all()

    tab.deleteLater()


def test_mainwindow_menus():
    """Verify that MainWindow has 'Archivo' and 'Ayuda' menus with standard actions."""
    window = MainWindow()
    menu_bar = window.menuBar()
    actions = menu_bar.actions()
    
    # We should have Archivo and Ayuda
    menu_titles = [act.text() for act in actions]
    assert 'Archivo' in menu_titles
    assert 'Ayuda' in menu_titles
    
    # Get Archivo menu actions
    archivo_act = next(act for act in actions if act.text() == 'Archivo')
    archivo_menu = archivo_act.menu()
    archivo_actions = archivo_menu.actions()
    
    # Check "Abrir carpeta de resultados" and "Salir"
    archivo_action_texts = [act.text() for act in archivo_actions]
    assert 'Abrir carpeta de resultados' in archivo_action_texts
    assert 'Salir' in archivo_action_texts
    
    # Check shortcut for exit
    exit_action = next(act for act in archivo_actions if act.text() == 'Salir')
    assert exit_action.shortcut().toString() == 'Ctrl+Q'
    
    # Get Ayuda menu actions
    ayuda_act = next(act for act in actions if act.text() == 'Ayuda')
    ayuda_menu = ayuda_act.menu()
    ayuda_actions = ayuda_menu.actions()
    ayuda_action_texts = [act.text() for act in ayuda_actions]
    assert 'Documentacion' in ayuda_action_texts
    assert 'Acerca de' in ayuda_action_texts
    assert 'Buscar actualizaciones' in ayuda_action_texts
    
    window.deleteLater()




