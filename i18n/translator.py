"""Custom Translator Function"""

from dataclasses import dataclass
from qgis.PyQt.QtCore import QCoreApplication  # type: ignore[reportMissingTypeStubs]

@dataclass
class Context:
    menu_main: str = "Main Menu"
    menu_tip: str = "Menu Tip"
    menu_whats: str = "Menu Whats

def tr(context: str, message: str) -> str:
    """Custom Translator Function"""
    
    if context == "Menu_main":
        return QCoreApplication.translate("Menu_main", message)
    if context == "Menu_tip":
        return QCoreApplication.translate("Menu_tip", message)
    if context == "Menu_whats":
        return QCoreApplication.translate("Menu_whats", message)
    if context == "UserError":
        return QCoreApplication.translate("UserError", message)

    return message
