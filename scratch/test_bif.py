import os
import sys
# Set Qt offscreen platform
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PyQt6.QtWidgets import QApplication, QMessageBox
app = QApplication.instance() or QApplication([])

# Mock QMessageBox.critical to prevent blocking
QMessageBox.critical = lambda parent, title, text, *args, **kwargs: print(f"CRITICAL DIALOG: {title} - {text}")

from ui.tab_controls import TabBifurcationWidget

print("Initializing TabBifurcationWidget...")
tab = TabBifurcationWidget()

# Test with a system without coexisting attractors, e.g. rossler
print("\nTesting Rossler (no coexisting)...")
tab.param_panel.system_combo.setCurrentIndex(tab.param_panel.system_combo.findData('rossler'))
print("Current system:", tab.param_panel.current_system_key())
print("Coex box enabled:", tab.coex_box.isEnabled())
print("chk_compare checked:", tab.chk_compare.isChecked())
print("Running bifurcation...")
tab.run_bifurcation()
print("Warning text:", tab.lbl_warning.text())

# Test with a system with coexisting attractors, e.g. lorenz
print("\nTesting Lorenz (with coexisting, comparison checked = False)...")
tab.param_panel.system_combo.setCurrentIndex(tab.param_panel.system_combo.findData('lorenz'))
print("Current system:", tab.param_panel.current_system_key())
print("Coex box enabled:", tab.coex_box.isEnabled())
print("chk_compare checked:", tab.chk_compare.isChecked())
print("Running bifurcation...")
tab.run_bifurcation()
print("Warning text:", tab.lbl_warning.text())

# Test with a system with coexisting attractors, e.g. lorenz, comparison checked = True
print("\nTesting Lorenz (with coexisting, comparison checked = True)...")
tab.chk_compare.setChecked(True)
print("chk_compare checked:", tab.chk_compare.isChecked())
print("Running bifurcation...")
tab.run_bifurcation()
print("Warning text:", tab.lbl_warning.text())

print("\nDone!")
