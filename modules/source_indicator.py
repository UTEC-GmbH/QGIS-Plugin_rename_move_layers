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


class LayerLocationIndicator(QgsLayerTreeViewIndicator):
    """A layer tree view indicator for data source location."""

    def __init__(self, parent: QgsLayerTreeView) -> None:
        """Initialize the indicator."""
        super().__init__(parent)
        self.view: QgsLayerTreeView = parent

    def id(self) -> str:
        """Return the unique identifier for this indicator."""
        return "LayerLocationIndicator"

    def willShow(self, node: "QgsLayerTreeNode") -> bool:  # type: ignore[override] # noqa: N802
        """Determine if the indicator should be shown for a given node."""
        return self.view.layerForNode(node) is not None

    def paint(
        self,
        painter: "QPainter",
        option: "QStyleOptionViewItem",
        index: "QModelIndex",
    ) -> None:
        """Paint the indicator icon."""
        node = self.view.index2node(index)
        if (layer := self.view.layerForNode(node)) is None:
            return

        location = ge.get_layer_location(layer)
        if emoji := LOCATION_EMOJI_MAP.get(location):
            painter.drawText(option.rect, int(Qt.AlignCenter), emoji)

    def toolTip(self, index: "QModelIndex") -> str:  # type: ignore[override]  # noqa: N802
        """Provide a tooltip for the indicator."""
        node = self.view.index2node(index)
        if (layer := self.view.layerForNode(node)) is None:
            return ""
        location = ge.get_layer_location(layer)
        return LOCATION_TOOLTIP_MAP.get(location, "")
