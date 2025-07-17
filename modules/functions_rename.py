"""Module: functions_rename.py

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

from .functions_general import (
    display_summary_message,
    generate_summary_message,
    get_current_project,
    get_selected_layers,
)

if TYPE_CHECKING:
    from qgis.core import QgsLayerTree, QgsLayerTreeNode


def fix_layer_name(name: str) -> str:
    """Fix encoding mojibake and sanitize a string to be a valid layer name.

    This function first attempts to fix a common mojibake encoding issue,
    where a UTF-8 string was incorrectly decoded as cp1252
    (for example: 'Ãœ' becomes 'Ü').
    It then sanitizes the string to remove or replace characters
    that might be problematic in layer names,
    especially for file-based formats or databases.

    :param name: The potentially garbled and raw layer name.
    :returns: A fixed and sanitized version of the name.
    """
    fixed_name: str = name
    with contextlib.suppress(UnicodeEncodeError):
        fixed_name = name.encode("cp1252").decode("utf-8")

    # Remove or replace problematic characters
    sanitized_name: str = re.sub(r'[<>:"/\\|?*,]+', "_", fixed_name)

    return sanitized_name


def prepare_rename_plan(plugin: QgisInterface) -> tuple[list, list, list, list]:
    """Rename the selected layers to their parent group names.

    Process all selected layers and provides a single summary message at the end.
    """
    layers_to_process: list[QgsMapLayer] = get_selected_layers(plugin)

    rename_plan: list = []  # List of (layer, old_name, new_name)
    failed_renames: list = []  # List of layer names that could not be renamed
    skipped_layers: list[str] = []  # List of layer names that are not in a group
    error_layers: list[str] = []  # List of layer names that could not be found

    project: QgsProject = get_current_project(plugin)

    root: QgsLayerTree | None = project.layerTreeRoot()
    if root is None:
        error_msg: str = "No Layer Tree is available."
        plugin.iface.messageBar().pushMessage("Error", error_msg, level=Qgis.Critical)
        raise RuntimeError(error_msg)

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

    return rename_plan, skipped_layers, failed_renames, error_layers


def execute_rename_plan(rename_plan: list) -> list:
    """Execute the renaming of layers based on a provided plan.

    This function iterates through the rename_plan, renaming each layer
    to its new name. If a rename operation fails (e.g., due to a duplicate
    name), it catches the RuntimeError and records the failure.

    :param rename_plan: A list of tuples, each containing (layer, old_name, new_name).
    :returns: A list of tuples, each detailing a failed rename operation
              in the format (old_name, new_name, error_message).
    """
    failed_renames: list = []

    for layer, old_name, new_layer_name in rename_plan:
        try:
            layer.setName(new_layer_name)
        except RuntimeError as e:  # noqa: PERF203
            # If setName fails, the layer name is unchanged.
            failed_renames.append((old_name, new_layer_name, str(e)))

    return failed_renames


def rename_layers(plugin: QgisInterface) -> None:
    """Orchestrates the renaming of selected layers to their parent group names."""

    # --- 1. Gather information and plan actions ---

    plan = prepare_rename_plan(plugin)

    if not plan:
        return  # Early exit if no plan could be prepared

    rename_plan, skipped_layers, failed_renames, error_layers = plan

    # --- 2. Execute actions ---
    failed_renames = execute_rename_plan(rename_plan)

    # --- 3. Report summary ---
    successful_count: int = len(rename_plan) - len(failed_renames)
    message, level = generate_summary_message(
        successes=successful_count,
        skipped=skipped_layers,
        failures=failed_renames,
        not_found=error_layers,
        action="Renamed",
    )

    display_summary_message(plugin, message, level)
