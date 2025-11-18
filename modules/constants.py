"""Module: constants.py

This module contains shared constants and enumerations used across the plugin.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from qgis.core import Qgis
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

PLUGIN_DIR: Path = Path(__file__).parent.parent

EMPTY_LAYER_NAME: str = "empty layer"

GEOMETRY_SUFFIX_MAP: dict[Qgis.GeometryType, str] = {
    Qgis.GeometryType.Line: "l",
    Qgis.GeometryType.Point: "pt",
    Qgis.GeometryType.Polygon: "pg",
}


@dataclass
class LayerLocationInfo:
    """Holds display information for a layer's location."""

    icon: QIcon
    _tooltip_factory: Callable[[], str]

    @property
    def tooltip(self) -> str:
        """Generate and return the translated tooltip.

        Returns:
            The translated tooltip string.
        """
        return self._tooltip_factory()


# fmt: off
# ruff: noqa: E501
class LayerLocation(LayerLocationInfo, Enum):
    """Enumeration for layer locations with associated display info."""

    CLOUD = (
        QIcon(str(PLUGIN_DIR / "icons" / "location_cloud.svg")),
        lambda: QCoreApplication.translate("LayerLocation", "<p>🔗<b>Cloud Layer</b>🔗</p>This layer is from a cloud-based service or database.<br><i>(Plugin: UTEC Layer Tools)</i>"),
    )
    EMPTY = (
        QIcon(str(PLUGIN_DIR / "icons" / "location_empty.svg")),
        lambda: QCoreApplication.translate("LayerLocation", "<p>❓<b>Empty Layer</b>❓</p>This Layer does not contain any objects.<br><i>(Plugin: UTEC Layer Tools)</i>"),
    )
    EXTERNAL = (
        QIcon(str(PLUGIN_DIR / "icons" / "location_external.svg")),
        lambda: QCoreApplication.translate("LayerLocation", "<p>💥💥💥<b>Caution</b>💥💥💥</p>This layer is stored outside the project folder. Please move to the project folder.<br><i>(Plugin: UTEC Layer Tools)</i>"),
    )
    FOLDER_NO_GPKG = (
        QIcon(str(PLUGIN_DIR / "icons" / "location_folder_no_gpkg.svg")),
        lambda: QCoreApplication.translate("LayerLocation", "<p>⚠️<b>Layer in Project Folder but not GeoPackage</b>⚠️</p>This layer is stored in the project folder, but not in a GeoPackage. Consider saving to the Project-GeoPackage (a GeoPackage with the same name as the project file).<br><i>(Plugin: UTEC Layer Tools)</i>"),
    )
    GPKG_FOLDER = (
        QIcon(str(PLUGIN_DIR / "icons" / "location_gpkg_folder.svg")),
        lambda: QCoreApplication.translate("LayerLocation", "<p>⚠️<b>Layer in GeoPackge in Project Folder</b>⚠️</p>This layer is stored in a GeoPackage in the project folder, but not in the Project-GeoPackage. Consider saving to the Project-GeoPackage (a GeoPackage with the same name as the project file).<br><i>(Plugin: UTEC Layer Tools)</i>"),
    )
    GPKG_PROJECT = (
        QIcon(str(PLUGIN_DIR / "icons" / "location_gpkg_project.svg")),
        lambda: QCoreApplication.translate("LayerLocation", "<p>👍<b>Layer in Project-Geopackage</b>👍</p>This layer is stored in the Project-GeoPackage (a GeoPackage with the same name as the project file).<br><i>(Plugin: UTEC Layer Tools)</i>"),
    )
    UNKNOWN = (
        QIcon(str(PLUGIN_DIR / "icons" / "location_unknown.svg")),
        lambda: QCoreApplication.translate("LayerLocation", "<p>❓<b>Data Source Unknown</b>❓</p>The data source of this Layer could not be determined.<br><i>(Plugin: UTEC Layer Tools)</i>"),
    )
# fmt: on
