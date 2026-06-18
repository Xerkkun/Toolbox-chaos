from __future__ import annotations

import os
import pytest
from PyQt6.QtWidgets import QApplication, QPushButton

# Setup QApplication offscreen for testing
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
_app = QApplication.instance() or QApplication([])

from ui.main_window import MainWindow
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
)
from core.lorenz import SYSTEM_REGISTRY
from core.coexistence import load_coexisting_attractors


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
    from PyQt6.QtWidgets import QMessageBox
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
    from PyQt6.QtWidgets import QMessageBox
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
    from PyQt6.QtWidgets import QMessageBox
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



