"""Module: functions.py

This module contains the function for renaming and moving layers
in a QGIS project based on their group names.
"""

from typing import TYPE_CHECKING

from qgis.core import (
    Qgis,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayer,
    QgsProject,
)
from qgis.gui import QgisInterface

if TYPE_CHECKING:
    from qgis._core import QgsLayerTree


def get_selected_layers(plugin: QgisInterface) -> list[QgsMapLayer]:
    """Collect all layers selected in the QGIS layer tree view.

    :returns: A list of selected QgsMapLayer objects.
    """
    selected_layers: set[QgsMapLayer] = set()
    selected_nodes = plugin.iface.layerTreeView().selectedNodes()

    for node in selected_nodes:
        if isinstance(node, QgsLayerTreeGroup):
            # If a group is selected, add all its layers recursively.
            for layer_node in node.findLayers():
                selected_layers.add(layer_node.layer())
        elif isinstance(node, QgsLayerTreeLayer):
            # Add the single selected layer.
            selected_layers.add(node.layer())

    return list(selected_layers)


def rename_layers(plugin: QgisInterface) -> None:
    """Rename the selected layers to their parent group names.

    Process all selected layers and provides a single summary message at the end.
    """
    layers_to_process: list[QgsMapLayer] = get_selected_layers(plugin)
    if not layers_to_process:
        plugin.iface.messageBar().pushMessage(
            "Warning", "No layers or groups selected.", level=Qgis.Warning
        )
        return

    # --- 1. Gather information and plan actions ---
    rename_plan: list = []  # List of (layer, old_name, new_name)
    skipped_layers: list[str] = []  # List of layer names that are not in a group
    error_layers: list[str] = []  # List of layer names that could not be found

    project: QgsProject | None = QgsProject.instance()
    if project is None:
        # Handle the case where no project is open or QGIS environment is not set up
        plugin.iface.messageBar().pushMessage(
            "Error", "No QGIS project is currently open.", level=Qgis.Critical
        )
        return

    root: QgsLayerTree = project.layerTreeRoot()

    for layer in layers_to_process:
        node: QgsLayerTreeLayer = root.findLayer(layer.id())
        if not node:
            error_layers.append(layer.name())
            continue

        parent = node.parent()
        if isinstance(parent, QgsLayerTreeGroup):
            group_name: str = parent.name()
            current_name: str = layer.name()
            new_name: str = group_name.encode("latin-1").decode("utf-8", "ignore")

            if current_name != new_name:
                rename_plan.append((layer, current_name, new_name))
        else:
            skipped_layers.append(layer.name())

    # --- 2. Execute actions ---
    for layer, _, new_name in rename_plan:
        layer.setName(new_name)

    # --- 3. Report summary ---
    if not any([rename_plan, skipped_layers, error_layers]):
        plugin.iface.messageBar().pushMessage(
            "Info",
            "All selected layers already have the correct names.",
            level=Qgis.Info,
            duration=5,
        )
        return

    message_parts: list[str] = []
    level = Qgis.Success
    if rename_plan:
        message_parts.append(f"Renamed {len(rename_plan)} layer(s).")
    if skipped_layers:
        message_parts.append(f"Skipped {len(skipped_layers)} layer(s) not in a group.")
        level = Qgis.Warning
    if error_layers:
        message_parts.append(
            f"Could not find {len(error_layers)} layer(s) in the layer tree."
        )
        level = Qgis.Critical

    plugin.iface.messageBar().pushMessage(
        "Rename Complete", " ".join(message_parts), level=level, duration=10
    )
