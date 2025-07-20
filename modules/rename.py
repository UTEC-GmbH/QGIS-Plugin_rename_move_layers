"""Module: functions_rename.py

This module contains the function for renaming and moving layers
in a QGIS project based on their group names.
"""

import contextlib
import re
from collections import defaultdict
from typing import TYPE_CHECKING

from qgis.core import (
    Qgis,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayer,
    QgsMessageLog,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgisInterface

from .general import (
    EMPTY_LAYER_NAME,
    GEOMETRY_SUFFIX_MAP,
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
    """Prepare a plan to rename selected layers based on their parent group.

    Empty vector layers are planned to be renamed to 'empty layer'. For other
    layers, the new name is based on their parent group name.

    If multiple layers would be renamed to the same name (e.g., they are in
    the same group, or multiple layers are empty), a geometry type suffix is
    appended to differentiate them.
    """
    layers_to_process: list[QgsMapLayer] = get_selected_layers(plugin)

    # Using defaultdict to group layers by their prospective new name
    potential_renames = defaultdict(list)
    skipped_layers: list[str] = []
    error_layers: list[str] = []

    project: QgsProject = get_current_project(plugin)
    root: QgsLayerTree | None = project.layerTreeRoot()
    if root is None:
        error_msg: str = "No Layer Tree is available."
        QgsMessageLog.logMessage(error_msg, "Error", level=Qgis.Critical)
        raise RuntimeError(error_msg)

    for layer in layers_to_process:
        # If a vector layer is empty, plan to rename it to "empty layer".
        if isinstance(layer, QgsVectorLayer) and layer.featureCount() == 0:
            potential_renames[EMPTY_LAYER_NAME].append(layer)
            continue

        node: QgsLayerTreeLayer | None = root.findLayer(layer.id())
        if not node:
            error_layers.append(layer.name())
            continue

        parent: QgsLayerTreeNode | None = node.parent()
        if isinstance(parent, QgsLayerTreeGroup):
            raw_group_name: str = parent.name()
            new_name_base: str = fix_layer_name(raw_group_name)
            potential_renames[new_name_base].append(layer)
        else:
            skipped_layers.append(layer.name())

    # Build the final rename plan, handling name collisions
    rename_plan = build_rename_plan(potential_renames)

    # The failed_renames list is populated by execute_rename_plan,
    # so initialize it as empty.
    failed_renames: list = []

    return rename_plan, skipped_layers, failed_renames, error_layers


def build_rename_plan(
    potential_renames: defaultdict[str, list[QgsMapLayer]],
) -> list[tuple[QgsMapLayer, str, str]]:
    """Build a list of rename operations, handling potential name collisions.

    This function processes a dictionary where keys are potential new layer names
    and values are lists of layers that would be renamed to that key. If a key
    maps to multiple layers (a name collision), it appends a geometry-specific
    suffix to each layer's new name to ensure uniqueness. If a layer's current
    name already matches the proposed new name, it is excluded from the plan.

    :param potential_renames: A dictionary grouping layers by their proposed new
        base name.
    :returns: A list of tuples, where each tuple contains the layer object, its
        original name, and its proposed new name. This list represents the
        final, conflict-resolved rename plan.
    """
    rename_plan: list[tuple[QgsMapLayer, str, str]] = []
    for new_name_base, layers in potential_renames.items():
        if len(layers) > 1:  # Name collision detected
            for layer in layers:
                suffix: str = (
                    ""
                    if new_name_base == EMPTY_LAYER_NAME
                    else geometry_type_suffix(layer)
                )
                final_new_name: str = f"{new_name_base}{suffix}"
                if layer.name() != final_new_name:
                    rename_plan.append((layer, layer.name(), final_new_name))
        else:  # No collision
            layer = layers[0]
            if layer.name() != new_name_base:
                rename_plan.append((layer, layer.name(), new_name_base))
    return rename_plan


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

    plan: tuple = prepare_rename_plan(plugin)
    if not plan:
        return  # Early exit if no plan could be prepared
    rename_plan, skipped_layers, failed_renames, error_layers = plan

    failed_renames: list = execute_rename_plan(rename_plan)

    successful_count: int = len(rename_plan) - len(failed_renames)
    message, level = generate_summary_message(
        successes=successful_count,
        skipped=skipped_layers,
        failures=failed_renames,
        not_found=error_layers,
        action="Renamed",
    )

    display_summary_message(plugin, message, level)


def geometry_type_suffix(layer: QgsMapLayer) -> str:
    """Get a short suffix for the geometry type of a layer.

    :param layer: The layer to get the geometry type suffix for.
    :returns: A string containing the geometry type suffix.
    """
    if not isinstance(layer, QgsVectorLayer):
        return ""

    geom_type: Qgis.GeometryType = QgsWkbTypes.geometryType(layer.wkbType())
    geom_display_string: str = QgsWkbTypes.geometryDisplayString(geom_type)

    return f" - {GEOMETRY_SUFFIX_MAP.get(geom_type, geom_display_string)}"
