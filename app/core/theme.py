from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

def apply_theme(app: QApplication, theme_name: str):
    theme_name = theme_name.lower()
    if theme_name == "dark" or theme_name == "system":
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#0b0f17"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#f1f5f9"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#0f172a"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#131b2a"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1e293b"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f1f5f9"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#f1f5f9"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#1e293b"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f1f5f9"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#f87171"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#3b82f6"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563eb"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        app.setPalette(palette)
        
    elif theme_name == "light":
        app.setStyle("Fusion")
        app.setPalette(app.style().standardPalette())
        
    else:
        # System default theme is kept
        pass
