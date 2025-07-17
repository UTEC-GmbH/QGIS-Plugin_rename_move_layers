"""Module: functions_general.py

This module contains the general functions.
"""

from qgis.core import (
    Qgis,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayer,
    QgsProject,
)
from qgis.gui import QgisInterface


def check_project(plugin: QgisInterface) -> QgsProject:
    """Check if a QGIS project is currently open and returns the project instance.

    If no project is open, displays an error message using the provided QGIS
    interface plugin.

    Args:
    plugin (QgisInterface): The QGIS interface plugin used to display messages.

    Returns:
    QgsProject | None: The current QGIS project instance if open, otherwise None.
    """
    project: QgsProject | None = QgsProject.instance()
    if project is None:
        error_msg: str = "No QGIS project is currently open."
        plugin.iface.messageBar().pushMessage("Error", error_msg, level=Qgis.Critical)
        raise RuntimeError(error_msg)

    return project


def get_selected_layers(plugin: QgisInterface) -> list[QgsMapLayer]:
    """Collect all layers selected in the QGIS layer tree view.

    :returns: A list of selected QgsMapLayer objects.
    """
    selected_layers: set[QgsMapLayer] = set()
    selected_nodes = plugin.iface.layerTreeView().selectedNodes()

    if not selected_nodes:
        error_msg: str = "No layers or groups selected."
        plugin.iface.messageBar().pushMessage("Warning", error_msg, level=Qgis.Warning)
        raise RuntimeError(error_msg)

    for node in selected_nodes:
        if isinstance(node, QgsLayerTreeGroup):
            # If a group is selected, add all its layers recursively.
            for layer_node in node.findLayers():
                selected_layers.add(layer_node.layer())
        elif isinstance(node, QgsLayerTreeLayer):
            # Add the single selected layer.
            selected_layers.add(node.layer())

    return list(selected_layers)


def report_summary(
    plugin: QgisInterface,
    rename_plan: list,
    skipped_layers: list,
    failed_renames: list,
    error_layers: list,
) -> None:
    """Report a summary of the rename operation to the user.

    This function consolidates the results of the rename operation,
    including successful renames, skipped layers, failures, and errors.
    It generates a user-friendly summary message and displays it via the
    QGIS message bar.

    :param plugin: The QGIS plugin interface for interacting with QGIS.
    :param rename_plan: A list of successful rename operations.
    :param skipped_layers: A list of layer names that were skipped because
                           they were not in a group.
    :param failed_renames: A list of tuples, each detailing a failed rename
                           operation in the format
                           (old_name, new_name, error_message).
    :param error_layers: A list of layer names that could not be found in
                         the layer tree.
    :returns: None. Displays a summary message in the QGIS message bar.
    """

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
        append_message_parts(rename_plan, message_parts, "Renamed ", ".")
    if skipped_layers:
        append_message_parts(
            skipped_layers,
            message_parts,
            "Skipped ",
            " that are not in a group.",
        )
        level = Qgis.Warning
    if failed_renames:
        append_message_parts(failed_renames, message_parts, "Could not rename ", ".")
        level = Qgis.Warning
    if error_layers:
        append_message_parts(
            error_layers,
            message_parts,
            "Could not find ",
            " in the layer tree.",
        )
        level = Qgis.Critical

    plugin.iface.messageBar().pushMessage(
        "Rename Complete", " ".join(message_parts), level=level, duration=10
    )


def append_message_parts(
    layer_list: list, message_parts: list, before: str, after: str
) -> None:
    """Append a message part to the message parts list.

    This function creates a user-friendly message string based on the number
    of items in `layer_list` and appends it to `message_parts`. It handles
    pluralization and formats the message with provided prefixes and suffixes.

    :param layer_list: A list of items (e.g., layer names or tuples of rename operations).
                       The length of this list determines the quantity mentioned in the message.
    :param message_parts: A list that accumulates the parts of the overall message.
                          The new part will be appended to this list.
    :param before: The string to prepend to the count of items (e.g., "Renamed ").
    :param after: The string to append after the item count and optional pluralization suffix (e.g., " layers.").
    :returns: None. Modifies `message_parts` in place.
    """
    rename_count: int = len(layer_list)
    plural_suffix: str = "s" if rename_count != 1 else ""
    message_parts.append(f"{before}{rename_count} layer{plural_suffix}{after}")
