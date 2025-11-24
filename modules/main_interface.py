"""Module: main_interface.py

This module manages the QgisInterface instance to avoid circular imports.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qgis.gui import QgisInterface


_iface: "QgisInterface | None" = None


def set_iface(iface_instance: "QgisInterface") -> None:
    """Set the global QgisInterface instance."""
    global _iface
    _iface = iface_instance


def get_iface() -> "QgisInterface | None":
    """Get the global QgisInterface instance."""
    return _iface
