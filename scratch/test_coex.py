import os
import sys
# Set Qt offscreen platform
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PyQt6.QtWidgets import QApplication, QMessageBox
app = QApplication.instance() or QApplication([])

# Mock QMessageBox.critical and information
QMessageBox.critical = lambda parent, title, text, *args, **kwargs: print(f"CRITICAL DIALOG: {title} - {text}")
QMessageBox.information = lambda parent, title, text, *args, **kwargs: print(f"INFO DIALOG: {title} - {text}")

from ui.tab_controls import TabCoexistenceWidget

print("Initializing TabCoexistenceWidget...")
tab = TabCoexistenceWidget()

print("Number of cases loaded:", len(tab.cases))
print("Case combo items count:", tab.case_combo.count())

if tab.case_combo.count() > 0:
    tab.case_combo.setCurrentIndex(0)
    print("Selected case:", tab.current_case().get('system_name'))
    print("Selected case attractors:", len(tab.current_case().get('attractors', [])))
    print("Attractor combo items count:", tab.attractor_combo.count())
    
    print("\nSimulating one...")
    tab.simulate_one()
    print("Simulated one successfully!")
    
    print("\nSimulating all...")
    tab.simulate_all()
    print("Simulated all successfully!")

print("\nDone!")
