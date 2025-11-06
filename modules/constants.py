"""Module: constants.py

This module contains shared constants used across the plugin to avoid
circular imports.
"""

from qgis.core import Qgis

EMPTY_LAYER_NAME: str = "empty layer"

GEOMETRY_SUFFIX_MAP: dict[Qgis.GeometryType, str] = {
    Qgis.GeometryType.Line: "l",
    Qgis.GeometryType.Point: "pt",
    Qgis.GeometryType.Polygon: "pg",
}
