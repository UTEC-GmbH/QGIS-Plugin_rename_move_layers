"""Module: indicator.py

This module contains the logic for a custom layer tree view indicator
that marks layers with their data source location.
"""

from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

from qgis.core import QgsMapLayer, QgsProject, QgsVectorLayer
from qgis.gui import QgsLayerTreeView, QgsLayerTreeViewIndicator
from qgis.PyQt.QtCore import QCoreApplication, Qt

from .geopackage import project_gpkg

if TYPE_CHECKING:
    from qgis.core import QgsLayerTreeNode, QgsProject
    from qgis.PyQt.QtCore import QModelIndex
    from qgis.PyQt.QtGui import QPainter
    from qgis.PyQt.QtWidgets import QStyleOptionViewItem


class LayerLocation(Enum):
    """Enumeration for layer data source locations."""

    IN_PROJECT_GPKG = auto()
    IN_PROJECT_FOLDER = auto()
    EXTERNAL = auto()
    NON_FILE = auto()  # For web services, databases, etc.
    UNKNOWN = auto()


LOCATION_EMOJI_MAP: dict[LayerLocation, str] = {
    LayerLocation.IN_PROJECT_GPKG: "📦",
    LayerLocation.IN_PROJECT_FOLDER: "📂",
    LayerLocation.EXTERNAL: "",
    LayerLocation.NON_FILE: "☁️",
}

# fmt: off
# ruff: noqa: E501
TT_GPKG: str = QCoreApplication.translate("LayerLocation", "Layer is stored in the project GeoPackage.")
TT_FOLDER: str = QCoreApplication.translate("LayerLocation", "Layer is stored in the project folder.")
TT_EXTERNAL: str = QCoreApplication.translate("LayerLocation", "Layer data source is outside the project folder.")
TT_NON_FILE: str = QCoreApplication.translate("LayerLocation", "Layer is from a web service or database.")
# fmt: on

LOCATION_TOOLTIP_MAP: dict[LayerLocation, str] = {
    LayerLocation.IN_PROJECT_GPKG: TT_GPKG,
    LayerLocation.IN_PROJECT_FOLDER: TT_FOLDER,
    LayerLocation.EXTERNAL: TT_EXTERNAL,
    LayerLocation.NON_FILE: TT_NON_FILE,
}


def get_layer_location(
    layer: QgsMapLayer, project_dir: Path, gpkg_path: Path | None
) -> LayerLocation:
    """Determine the location of the layer's data source.

    Args:
        layer: The QGIS map layer to check.
        project_dir: The path to the project's directory.
        gpkg_path: The path to the project's GeoPackage, or None if not available.

    Returns:
        A LayerLocation enum member indicating the layer's data source location.
    """
    if not isinstance(layer, QgsVectorLayer):
        return LayerLocation.UNKNOWN

    source: str = layer.source()
    path_part: str = source.split("|")[0]

    if not path_part or not Path(path_part).exists():
        return LayerLocation.NON_FILE

    try:
        layer_path: Path = Path(path_part).resolve()

        if gpkg_path and layer_path == gpkg_path.resolve():
            return LayerLocation.IN_PROJECT_GPKG

        if layer_path.is_relative_to(project_dir):
            return LayerLocation.IN_PROJECT_FOLDER

        return LayerLocation.EXTERNAL

    except (ValueError, RuntimeError):
        # Catches errors from invalid paths or if paths are on different drives
        return LayerLocation.EXTERNAL


class LayerLocationIndicator(QgsLayerTreeViewIndicator):
    """A layer tree view indicator for data source location.

    This indicator adds an icon to layers in the layer tree if their data
    source is located outside the current project's directory.
    """

    def __init__(self, view: QgsLayerTreeView) -> None:
        """Initialize the indicator.

        Args:
            view: The layer tree view to which this indicator is attached.
        """
        super().__init__(view)
        self.view: QgsLayerTreeView = view
        self.location_cache: dict[str, LayerLocation] = {}

    def id(self) -> str:
        """Return the unique identifier for this indicator."""
        return "LayerLocationIndicator"

    def willShow(self, node: "QgsLayerTreeNode") -> bool:  # noqa: N802
        """Determine if the indicator should be shown for a given node.

        Args:
            node: The layer tree node to check.

        Returns:
            True if the node is a layer with a known location, False otherwise.
        """
        project: QgsProject = self.view.model().layerTreeRoot().project()
        project_path_str: str = project.fileName()

        if not project_path_str:
            self.location_cache.clear()
            return False  # Cannot determine if external without a project path

        project_dir: Path = Path(project_path_str).parent.resolve()
        try:
            gpkg_path: Path | None = project_gpkg()
        except Exception:
            gpkg_path = None

        layer: QgsMapLayer | None = self.view.layerForNode(node)
        if layer is None:
            return False

        # Cache the location to avoid re-calculating it in the paint method
        location = get_layer_location(layer, project_dir, gpkg_path)
        self.location_cache[layer.id()] = location

        return location in LOCATION_EMOJI_MAP

    def toolTip(self, index: "QModelIndex") -> str:
        """Provide a tooltip for the indicator.

        Args:
            index: The model index of the item.

        Returns:
            The tooltip string for the indicator.
        """
        node = self.view.index2node(index)
        if (layer := self.view.layerForNode(node)) is None:
            return ""

        location = self.location_cache.get(layer.id(), LayerLocation.UNKNOWN)
        return LOCATION_TOOLTIP_MAP.get(location, "")

    def paint(
        self,
        painter: "QPainter",
        option: "QStyleOptionViewItem",
        index: "QModelIndex",
    ) -> None:
        """Paint the indicator icon.

        Args:
            painter: The QPainter to use for drawing.
            option: The style options for the item.
            index: The model index of the item.
        """
        node = self.view.index2node(index)
        if (layer := self.view.layerForNode(node)) is None:
            return

        location = self.location_cache.get(layer.id(), LayerLocation.UNKNOWN)
        if emoji := LOCATION_EMOJI_MAP.get(location):
            painter.drawText(option.rect, int(Qt.AlignCenter), emoji)
