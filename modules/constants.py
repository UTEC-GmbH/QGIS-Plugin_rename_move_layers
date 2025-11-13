"""Module: constants.py

This module contains shared constants and enumerations used across the plugin.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from PyQt5.QtGui import QIcon
from qgis.core import Qgis
from qgis.PyQt.QtCore import QCoreApplication

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
        QIcon(":/compiled_resources_LayerTools/icons/location_cloud.svg"),
        lambda: QCoreApplication.translate("LayerLocation", "🔗<b>Cloud Layer</b>🔗<br>This layer is from a cloud-based service or database."),
    )
    EMPTY = (
        QIcon(":/compiled_resources_LayerTools/icons/location_empty.svg"),
        lambda: QCoreApplication.translate("LayerLocation", "❓<b>Empty Layer</b>❓<br>This Layer does not contain any objects."),
    )
    EXTERNAL = (
        QIcon(":/compiled_resources_LayerTools/icons/location_external.svg"),
        lambda: QCoreApplication.translate("LayerLocation", "💥💥💥<b>Caution</b>💥💥💥<br>This layer is stored outside the project folder. Please move to the project folder."),
    )
    FOLDER_NO_GPKG = (
        QIcon(":/compiled_resources_LayerTools/icons/location_folder_no_gpkg.svg"),
        lambda: QCoreApplication.translate("LayerLocation", "⚠️<b>Layer in Project Folder but not GeoPackage</b>⚠️<br>This layer is stored in the project folder, but not in a GeoPackage. Consider saving to the Project-GeoPackage (a GeoPackage with the same name as the project file)."),
    )
    GPKG_FOLDER = (
        QIcon(":/compiled_resources_LayerTools/icons/location_gpkg_folder.svg"),
        lambda: QCoreApplication.translate("LayerLocation", "⚠️<b>Layer in GeoPackge in Project Folder</b>⚠️<br>This layer is stored in a GeoPackage in the project folder, but not in the Project-GeoPackage. Consider saving to the Project-GeoPackage (a GeoPackage with the same name as the project file)."),
    )
    GPKG_PROJECT = (
        QIcon(":/compiled_resources_LayerTools/icons/location_gpkg_project.svg"),
        lambda: QCoreApplication.translate("LayerLocation", "👍<b>Layer in Project-Geopackage</b>👍<br>This layer is stored in the Project-GeoPackage (a GeoPackage with the same name as the project file)."),
    )
    UNKNOWN = (
        QIcon(":/compiled_resources_LayerTools/icons/location_unknown.svg"),
        lambda: QCoreApplication.translate("LayerLocation", "❓<b>Data Source Unknown</b>❓<br>The data source of this Layer could not be determined."),
    )
# fmt: on
