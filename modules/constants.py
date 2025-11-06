"""Module: constants.py

This module contains shared constants and enumerations used across the plugin.
"""

from dataclasses import dataclass
from enum import Enum

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

    emoji: str = ""
    tooltip: str = ""


# fmt: off
# ruff: noqa: E501
class LayerLocation(LayerLocationInfo, Enum):
    """Enumeration for layer locations with associated display info."""

    IN_PROJECT_GPKG = (
        "✅",
        QCoreApplication.translate("LayerLocation", "Layer is stored in the project GeoPackage."),
    )
    IN_PROJECT_FOLDER = (
        "📂",
        QCoreApplication.translate("LayerLocation", "Layer is stored in the project folder."),
    )
    EXTERNAL = (
        "‼️☠️‼️",
        QCoreApplication.translate("LayerLocation", "Layer data source is outside the project folder."),
    )
    NON_FILE = (
        "☁️",
        QCoreApplication.translate("LayerLocation", "Layer is from a web service or database."),
    )
    UNKNOWN = ()
# fmt: on
