"""Mark the source of the data."""

from typing import TYPE_CHECKING

from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from qgis.core import QgsLayerTreeLayer, QgsLayerTreeNode
from qgis.gui import QgsLayerTreeView
from qgis.PyQt.QtCore import QEvent, QModelIndex, Qt

from .constants import LayerLocation
from .general import get_layer_location
from .logs_and_errors import log_debug

if TYPE_CHECKING:
    from qgis.core import QgsMapLayer
LOCATION_ICON_MAP: dict[str, QIcon] = {
    "IN_PROJECT_GPKG": QIcon(":/compiled_resources/icons/gpkg.svg"),
    "IN_PROJECT_FOLDER": QIcon(":/compiled_resources/icons/folder.svg"),
    "EXTERNAL": QIcon(":/compiled_resources/icons/external.svg"),
    "NON_FILE": QIcon(":/compiled_resources/icons/cloud.svg"),
    "UNKNOWN": QIcon(":/compiled_resources/icons/unknown.svg"),
}


class LayerLocationDelegate(QStyledItemDelegate):
    """A custom delegate to draw location icons in the layer tree view."""

    def __init__(
        self, view: QgsLayerTreeView, base_delegate: QStyledItemDelegate
    ) -> None:
        """Initialize the delegate."""
        super().__init__(view)
        self.view: QgsLayerTreeView = view
        self.base_delegate: QStyledItemDelegate = base_delegate

    def _overlay_rect(self, option: QStyleOptionViewItem):
        """Calculate the rectangle for the icon on the right side."""
        rect = option.rect
        # Reserve ~18px at the right edge for the indicator
        return rect.adjusted(rect.width() - 18, 1, -2, -1)

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:  # type: ignore[override]
        """Paint the delegate, adding the custom icon for layer nodes."""
        node: QgsLayerTreeNode = self.view.index2node(index)

        # Only attempt to draw icons for actual layer nodes, not groups
        if not isinstance(node, QgsLayerTreeLayer):
            self.base_delegate.paint(painter, option, index)
            return

        # Reserve space on the right for our icon by shrinking the area
        # available to the base delegate.
        icon_width = 18
        original_rect = option.rect
        option.rect = original_rect.adjusted(0, 0, -icon_width, 0)

        # Let the original delegate paint in the shrunken area
        self.base_delegate.paint(painter, option, index)

        layer: QgsMapLayer | None = node.layer()
        if not layer:
            return

        location: LayerLocation = get_layer_location(layer)
        key = location.name if isinstance(location, LayerLocation) else "UNKNOWN"
        icon = LOCATION_ICON_MAP.get(key)
        if icon is None:
            return

        painter.save()
        try:
            # Calculate the position for our icon in the reserved space
            icon_rect = original_rect.adjusted(
                original_rect.width() - icon_width, 0, 0, 0
            )
            overlay_rect = icon_rect.adjusted(1, 1, -2, -1)
            icon.paint(painter, overlay_rect, Qt.AlignCenter, QIcon.Normal, QIcon.On)
        finally:
            painter.restore()

    def helpEvent(
        self, event: QEvent, view, option: QStyleOptionViewItem, index: QModelIndex
    ) -> bool:  # type: ignore[override]
        """Provide a tooltip when hovering over the icon area."""
        node: QgsLayerTreeNode | None = self.view.index2node(index)

        if not node or not isinstance(node, QgsLayerTreeLayer):
            return self.base_delegate.helpEvent(event, view, option, index)

        layer: QgsMapLayer | None = node.layer()
        if layer is None:
            return self.base_delegate.helpEvent(event, view, option, index)

        if not self._overlay_rect(option).contains(event.pos()):
            return self.base_delegate.helpEvent(event, view, option, index)

        location = get_layer_location(layer)
        tooltip = location.tooltip or f"Layer: {layer.name()}"
        log_debug(f"Delegate: toolTip for layer={layer.name()} -> {tooltip}")
        view.setToolTip(tooltip)
        return True
