"""Module: functions.py

This module contains the function for renaming and moving layers
in a QGIS project based on their group names.
"""

import contextlib
import re
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
    from qgis._core import QgsLayerTree, QgsLayerTreeNode


def fix_layer_name(name: str) -> str:
    """Fix encoding mojibake and sanitize a string to be a valid layer name.

    This function first attempts to fix a common mojibake encoding issue,
    where a UTF-8 string was incorrectly decoded, and then sanitizes the
    string to remove or replace characters that might be problematic in layer
    names, especially for file-based formats or databases.

    :param name: The potentially garbled and raw layer name.
    :returns: A fixed and sanitized version of the name.
    """
    fixed_name: str = name
    with contextlib.suppress(UnicodeEncodeError):
        # This will fix strings that were incorrectly decoded as cp1252.
        # For example: 'Ãœ' becomes 'Ü', and 'Ã©' becomes 'é'.
        fixed_name = name.encode("cp1252").decode("utf-8")
    return re.sub(r'[<>:"/\\|?*]+', "_", fixed_name)


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
    failed_renames: list = []  # List of layer names that could not be renamed
    skipped_layers: list[str] = []  # List of layer names that are not in a group
    error_layers: list[str] = []  # List of layer names that could not be found

    project: QgsProject | None = QgsProject.instance()
    if project is None:
        # Handle the case where no project is open or QGIS environment is not set up
        plugin.iface.messageBar().pushMessage(
            "Error", "No QGIS project is currently open.", level=Qgis.Critical
        )
        return

    root: QgsLayerTree | None = project.layerTreeRoot()
    if root is None:
        plugin.iface.messageBar().pushMessage(
            "Error", "No Layer Tree is available.", level=Qgis.Critical
        )
        return

    for layer in layers_to_process:
        node: QgsLayerTreeLayer = root.findLayer(layer.id())
        if not node:
            error_layers.append(layer.name())
            continue

        parent: QgsLayerTreeNode | None = node.parent()
        if isinstance(parent, QgsLayerTreeGroup):
            raw_group_name: str = parent.name()
            current_layer_name: str = layer.name()
            new_layer_name: str = fix_layer_name(raw_group_name)

            if current_layer_name != new_layer_name:
                rename_plan.append((layer, current_layer_name, new_layer_name))
        else:
            skipped_layers.append(layer.name())

    # --- 2. Execute actions ---
    for layer, old_name, new_layer_name in rename_plan:
        try:
            layer.setName(new_layer_name)
        except RuntimeError as e:  # noqa: PERF203
            # If setName fails, the layer name is unchanged.
            failed_renames.append((old_name, new_layer_name, str(e)))

    # --- 3. Report summary ---
    if not rename_plan and not error_layers:
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
    if failed_renames:
        message_parts.append(f"Could not rename {len(failed_renames)} layer(s).")
        level = Qgis.Warning
    if error_layers:
        message_parts.append(
            f"Could not find {len(error_layers)} layer(s) in the layer tree."
        )
        level = Qgis.Critical

    plugin.iface.messageBar().pushMessage(
        "Rename Complete", " ".join(message_parts), level=level, duration=10
    )
