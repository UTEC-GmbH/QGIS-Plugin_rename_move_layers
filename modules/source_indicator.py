"""Mark the source of the data."""

from enum import Enum, auto

from qgis.PyQt.QtCore import QCoreApplication


class LayerLocation(Enum):
    """Enumeration for layer data source locations."""

    IN_PROJECT_GPKG = auto()
    IN_PROJECT_FOLDER = auto()
    EXTERNAL = auto()
    NON_FILE = auto()  # For web services, databases, etc.
    UNKNOWN = auto()


LOCATION_EMOJI_MAP: dict[LayerLocation, str] = {
    LayerLocation.IN_PROJECT_GPKG: "✅",
    LayerLocation.IN_PROJECT_FOLDER: "📂",
    LayerLocation.EXTERNAL: "‼️☠️‼️",
    LayerLocation.NON_FILE: "☁️",
}

# fmt: off
# ruff: noqa: E501
LOCATION_TOOLTIP_MAP: dict[LayerLocation, str] = {
    LayerLocation.IN_PROJECT_GPKG: QCoreApplication.translate("LayerLocation", "Layer is stored in the project GeoPackage."),
    LayerLocation.IN_PROJECT_FOLDER: QCoreApplication.translate("LayerLocation", "Layer is stored in the project folder."),
    LayerLocation.EXTERNAL: QCoreApplication.translate("LayerLocation", "Layer data source is outside the project folder."),
    LayerLocation.NON_FILE: QCoreApplication.translate("LayerLocation", "Layer is from a web service or database."),
}
# fmt: on
