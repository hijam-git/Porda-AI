"""
settingscss2.py - Settings UI Styling Module

This module contains CSS styling definitions for the Porda AI settings interface.
It provides a consistent visual theme and styling for all UI components in
the settings dialog, including buttons, labels, input fields, and containers.

@author Abdullah
@version 1.0
@since 2024
"""

css = """
QDialog {
    background-color: #f5f5f5;
}

QPushButton {
    padding: 8px;
    font-size: 16px;
    color: black;
    background-color: #f5f5f5;
    border: 1px solid blue;
    border-radius: 5px;
    margin: 1px;
}

QPushButton:hover {
    background-color: #e0e0e0;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QGroupBox {
    background-color: #f5f5f5;
    border: 1px solid #cccccc;
    border-radius: 5px;
    margin: 3px;
}

QLabel {
    font-size: 16px;
}

QSplitter {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 5px;
    margin: 5px;
}

QComboBox, QSpinBox, QDoubleSpinBox {
    padding: 5px;
    font-size: 18px;
    border: 1px solid #cccccc;
    border-radius: 5px;
}

QCheckBox, QRadioButton {
    font-size: 16px;
}
"""

