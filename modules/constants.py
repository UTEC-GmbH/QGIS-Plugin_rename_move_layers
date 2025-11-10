"""Module: constants.py

This module contains shared constants and enumerations used across the plugin.
"""

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
    tooltip: str


# fmt: off
# ruff: noqa: E501
class LayerLocation(LayerLocationInfo, Enum):
    """Enumeration for layer locations with associated display info."""

    IN_PROJECT_GPKG = (
        QIcon(":/compiled_resources_LayerTools/icons/location_gpkg.svg"),
        QCoreApplication.translate("LayerLocation", "Layer is stored in the project GeoPackage."),
    )
    IN_PROJECT_FOLDER = (
        QIcon(":/compiled_resources_LayerTools/icons/location_folder.svg"),
        QCoreApplication.translate("LayerLocation", "Layer is stored in the project folder. Consider saving to the GeoPackage."),
    )
    EXTERNAL = (
        QIcon(":/compiled_resources_LayerTools/icons/location_external.svg"),
        QCoreApplication.translate("LayerLocation", "Caution: Layer data source is outside the project folder. Please move to the project folder."),
    )
    NON_FILE = (
        QIcon(":/compiled_resources_LayerTools/icons/location_cloud.svg"),
        QCoreApplication.translate("LayerLocation", "Layer is from a web service or database."),
    )
    UNKNOWN = (
        QIcon(":/compiled_resources_LayerTools/icons/location_unknown.svg"),
        QCoreApplication.translate("LayerLocation", "Layer data source unknown."),
    )
# fmt: on
