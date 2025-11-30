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
    return str(plugin_dir / "resources" / name)


def _icon(filename: str) -> QIcon:
    """Create a QIcon from the icons directory."""
    return QIcon(get_resource_path(f"icons/{filename}"))


class _Icons:
    """Container for icon resources.

    Properties are defined for existing icons to enable auto-completion.
    New icons can be accessed dynamically via dot-notation
    (e.g. resources.icons.new_icon)
    which will map to 'icons/new_icon.svg'.
    """

    def __getattr__(self, name: str) -> QIcon:
        """Dynamically get an icon by name if it's not defined as a property."""
        return _icon(f"{name}.svg")

    @property
    def location_cloud(self) -> QIcon:
        return _icon("location_cloud.svg")

    @property
    def location_empty(self) -> QIcon:
        return _icon("location_empty.svg")

    @property
    def location_external(self) -> QIcon:
        return _icon("location_external.svg")

    @property
    def location_folder_no_gpkg(self) -> QIcon:
        return _icon("location_folder_no_gpkg.svg")

    @property
    def location_gpkg_folder(self) -> QIcon:
        return _icon("location_gpkg_folder.svg")

    @property
    def location_gpkg_project(self) -> QIcon:
        return _icon("location_gpkg_project.svg")

    @property
    def location_unknown(self) -> QIcon:
        return _icon("location_unknown.svg")

    @property
    def main_move(self) -> QIcon:
        return _icon("main_move.svg")

    @property
    def main_rename(self) -> QIcon:
        return _icon("main_rename.svg")

    @property
    def main_rename_move(self) -> QIcon:
        return _icon("main_rename_move.svg")

    @property
    def main_undo(self) -> QIcon:
        return _icon("main_undo.svg")

    @property
    def plugin_main_icon(self) -> QIcon:
        return _icon("plugin_main_icon.svg")


class _Resources:
    """Access point for plugin resources."""

    icons = _Icons()


# Global instance for easy access
resources = _Resources()
