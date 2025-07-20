"""Module: functions_general.py

This module contains the general functions.
"""

from typing import TYPE_CHECKING

from qgis.core import (
    Qgis,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayer,
    QgsProject,
    QgsVectorDataProvider,
    QgsVectorLayer,
)
from qgis.gui import QgisInterface

if TYPE_CHECKING:
    from qgis._core import QgsDataProvider


def get_current_project(plugin: QgisInterface) -> QgsProject:
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


def generate_summary_message(
    successes: int = 0,
    skipped: list | None = None,
    failures: list | None = None,
    not_found: list | None = None,
    action: str = "Operation",
) -> tuple[str, int]:
    """Generate a summary message for the user based on operation results.

    This function constructs a user-friendly message summarizing the outcome
    of a plugin operation (e.g., renaming, moving layers). It handles different
    result types (successes, skips, failures, not found) and pluralization
    to create grammatically correct and informative feedback.

    :param plugin: The QGIS plugin interface for interacting with QGIS.
    :param successes: The number of successful operations.
    :param skipped: A list of layer names that were skipped.
    :param failures: A list of tuples detailing failed operations,
                     (e.g., (old_name, new_name, error_message)).
    :param not_found: A list of layer names that could not be found.
    :param action: A string describing the action performed (e.g., "Renamed", "Moved").
    :returns: A tuple containing the summary message (str) and the message level (int).
    """
    message_parts: list[str] = []
    message_level: int = Qgis.Success
    plural: str = ""

    if successes:
        plural = "s" if successes > 1 else ""
        message_parts.append(f"{action} {successes} layer{plural}.")

    if skipped:
        plural = "s" if len(skipped) > 1 else ""
        message_parts.append(f"Skipped {len(skipped)} layer{plural}.")
        message_level = Qgis.Warning

    if failures:
        plural = "s" if len(failures) > 1 else ""
        message_parts.append(
            f"Could not {action.lower()} {len(failures)} layer{plural}."
        )
        message_level = Qgis.Warning

    if not_found:
        plural = "s" if len(not_found) > 1 else ""
        message_parts.append(f"Could not find {len(not_found)} layer{plural}.")
        message_level = Qgis.Critical

    if not message_parts:  # If no operations were reported
        message_parts.append(
            "No layers processed or all selected layers already have the desired state."
        )
        message_level = Qgis.Info

    return " ".join(message_parts), message_level


def display_summary_message(plugin: QgisInterface, message: str, level: int) -> None:
    """Display a summary message in the QGIS message bar.

    This function takes a message and a message level and displays them in the
    QGIS message bar using the provided plugin interface.

    :param plugin: The QGIS plugin interface for interacting with QGIS.
    :param message: The message string to display.
    :param level: The message level (e.g., Qgis.Success, Qgis.Warning, Qgis.Critical).
    :returns: None. Displays a message in the QGIS message bar.
    """
    plugin.iface.messageBar().pushMessage(
        "Operation Summary", message, level=level, duration=10
    )


def clear_attribute_table(layer: QgsMapLayer) -> None:
    """Clear the attribute table of a QGIS layer by deleting all columns.

    :param layer: The layer whose attribute table should be cleared.
    """
    if not isinstance(layer, QgsVectorLayer):
        # This function only applies to vector layers.
        return

    provider: QgsDataProvider | None = layer.dataProvider()
    if not provider:
        return

    # Check if the provider supports deleting attributes.
    if not provider.capabilities() & QgsVectorDataProvider.DeleteAttributes:
        return

    if field_indices := list(range(layer.fields().count())):
        provider.deleteAttributes(field_indices)
        layer.updateFields()
