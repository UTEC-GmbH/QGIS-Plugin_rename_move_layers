"""Helper module for accessing plugin resources."""

from pathlib import Path

from qgis.PyQt.QtGui import QIcon


def get_resource_path(name: str) -> str:
    """Get the absolute path to a resource file.

    Args:
        name: Relative path to the resource (e.g. 'icons/my_icon.svg')

    Returns:
        Absolute path to the resource file.
    """
    # This file is in modules/, so we go up one level to get to the plugin root
    plugin_dir = Path(__file__).parent.parent
    return str(plugin_dir / name)


def get_icon(name: str) -> QIcon:
    """Get a QIcon instance for a resource.

    Args:
        name: Relative path to the resource (e.g. 'icons/my_icon.svg')

    Returns:
        QIcon instance.
    """
    return QIcon(get_resource_path(name))
