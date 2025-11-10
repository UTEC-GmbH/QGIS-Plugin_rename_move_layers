"""Module: functions_general.py

This module contains the general functions.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from qgis.core import (
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayer,
    QgsProject,
    QgsVectorDataProvider,
    QgsVectorLayer,
)
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QCoreApplication

from .constants import EMPTY_LAYER_NAME
from .logs_and_errors import log_debug, raise_runtime_error, raise_user_error

if TYPE_CHECKING:
    from qgis.core import QgsDataProvider, QgsLayerTreeNode
    from qgis.gui import QgsLayerTreeView


iface: QgisInterface | None = None


def get_current_project() -> QgsProject:
    """Check if a QGIS project is currently open and returns the project instance.

    If no project is open, an error message is logged.

    Returns:
    QgsProject: The current QGIS project instance.
    """
    project: QgsProject | None = QgsProject.instance()
    if project is None:
        # fmt: off
        msg: str = QCoreApplication.translate("RuntimeError", "No QGIS project is currently open.")
        # fmt: on
        raise_runtime_error(msg)

    return project


def get_selected_layers() -> list[QgsMapLayer]:
    """Collect all layers selected in the QGIS layer tree view.

    :returns: A list of selected QgsMapLayer objects.
    """
    # fmt: off
    # ruff: noqa: E501
    no_interface:str = QCoreApplication.translate("RuntimeError", "QGIS interface not set.")
    no_layertree:str = QCoreApplication.translate("RuntimeError", "Could not get layer tree view.")
    no_selection:str = QCoreApplication.translate("RuntimeError", "No layers or groups selected.")
    # fmt: on

    if iface is None:
        raise_runtime_error(no_interface)

    layer_tree: QgsLayerTreeView | None = iface.layerTreeView()
    if not layer_tree:
        raise_runtime_error(no_layertree)

    selected_layers: set[QgsMapLayer] = set()
    selected_nodes: list[QgsLayerTreeNode] = layer_tree.selectedNodes()
    if not selected_nodes:
        raise_user_error(no_selection)

    for node in selected_nodes:
        if isinstance(node, QgsLayerTreeGroup):
            # If a group is selected, add all its layers that are not empty recursively.
            for layer_node in node.findLayers():
                layer: QgsMapLayer | None = layer_node.layer()
                if layer and layer.name() != EMPTY_LAYER_NAME:
                    selected_layers.add(layer_node.layer())
        elif all(
            [
                isinstance(node, QgsLayerTreeLayer),
                node.layer(),
                node.layer().name() != EMPTY_LAYER_NAME,
            ]
        ):
            # Add the single selected layer.
            selected_layers.add(node.layer())
        else:
            log_debug(f"Unexpected node type in selection: {type(node)}")

    return list(selected_layers)


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


def project_gpkg() -> Path:
    """Return the expected GeoPackage path for the current project without I/O side effects.

    Example: for a project 'my_project.qgz', returns 'my_project.gpkg' in the same directory.

    :returns: The Path object to the GeoPackage.
    :raises UserError: If the project is not saved.
    """
    project: QgsProject = get_current_project()
    project_path_str: str = project.fileName()
    if not project_path_str:
        # fmt: off
        msg: str = QCoreApplication.translate("UserError", "Project is not saved. Please save the project first.")
        # fmt: on
        raise_user_error(msg)

    project_path: Path = Path(project_path_str)
    gpkg_path: Path = project_path.with_suffix(".gpkg")

    # Do NOT create the file here (issue #3)
    return gpkg_path
