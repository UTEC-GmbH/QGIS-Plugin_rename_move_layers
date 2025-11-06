"""Mark the source of the data."""

from typing import TYPE_CHECKING

from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QStyleOptionViewItem
from qgis._core import QgsLayerTreeNode
from qgis.gui import QgsLayerTreeView, QgsLayerTreeViewIndicator
from qgis.PyQt.QtCore import QModelIndex, Qt

from .general import get_layer_location
from .logs_and_errors import log_debug

if TYPE_CHECKING:
    from qgis.core import QgsLayerTreeNode

    from .constants import LayerLocation


class LayerLocationIndicator(QgsLayerTreeViewIndicator):
    """A layer tree view indicator for data source location."""

    def __init__(self, parent: QgsLayerTreeView) -> None:
        """Initialize the indicator."""
        super().__init__(parent)
        self.view: QgsLayerTreeView = parent

    def id(self) -> str:
        """Return the unique identifier for this indicator."""
        return "LayerLocationIndicator"

    def willShow(self, node: "QgsLayerTreeNode") -> bool:  # noqa: N802
        """Determine if the indicator should be shown for a given node."""
        log_debug(f"willShow called for node: {node.name()}")
        return self.view.layerForNode(node) is not None

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        """Paint the indicator icon."""
        node: QgsLayerTreeNode | None = self.view.index2node(index)
        if (layer := self.view.layerForNode(node)) is None:
            return

        location: LayerLocation = get_layer_location(layer)
        log_debug(f"paint called for layer: {layer.name()} → {location.emoji}")
        if location.emoji:
            painter.drawText(option.rect, int(Qt.AlignCenter), location.emoji)

    def toolTip(self, index: QModelIndex) -> str:  # type: ignore[override]  # noqa: N802
        """Provide a tooltip for the indicator."""
        node: QgsLayerTreeNode | None = self.view.index2node(index)
        if (layer := self.view.layerForNode(node)) is None:
            return ""

        location: LayerLocation = get_layer_location(layer)
        return location.tooltip

    def refresh(self) -> None:
        """Force a repaint of the layer tree view to update the indicator."""
        if self.view and self.view.viewport():
            self.view.viewport().update()
