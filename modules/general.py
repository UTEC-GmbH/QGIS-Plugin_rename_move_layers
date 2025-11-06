"""Module: functions_general.py

This module contains the general functions.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from osgeo import ogr
from qgis.core import (
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayer,
    QgsProject,
    QgsVectorDataProvider,
    QgsVectorLayer,
)
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import (
    QCoreApplication,  # type: ignore[reportAttributeAccessIssue]
)

from .constants import EMPTY_LAYER_NAME, LayerLocation
from .logs_and_errors import log_debug, raise_runtime_error, raise_user_error

if TYPE_CHECKING:
    from qgis._core import QgsLayerTreeNode
    from qgis._gui import QgsLayerTreeView
    from qgis.core import QgsDataProvider

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
    """Check if a GeoPackage with the same name as the project
    exists in the project folder and creates it if not.

    Example: for a project 'my_project.qgz',
    it looks for 'my_project.gpkg' in the same directory.

    :returns: The Path object to the GeoPackage.
    :raises UserError: If the project is not saved.
    :raises IOError: If the GeoPackage file cannot be created.
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

    if not gpkg_path.exists():
        driver = ogr.GetDriverByName("GPKG")
        data_source = driver.CreateDataSource(str(gpkg_path))
        if data_source is None:
            # fmt: off
            msg: str = QCoreApplication.translate("RuntimeError", "Failed to create GeoPackage at: {0}").format(gpkg_path)
            # fmt: on
            raise_runtime_error(msg)

        # Dereference the data source to close the file and release the lock.
        data_source = None

    return gpkg_path


def get_layer_location(layer: "QgsMapLayer") -> "LayerLocation":
    """Determine the location of the layer's data source with caching.

    Args:
        layer: The QGIS map layer to check.

    Returns:
        A LayerLocation enum member indicating the layer's data source location.
    """

    if (project := get_current_project()) is None or not project.fileName():
        return LayerLocation.UNKNOWN

    project_dir: Path = Path(project.fileName()).parent.resolve()
    try:
        gpkg_path: Path | None = project_gpkg()
    except Exception:
        gpkg_path = None

    source: str = layer.source()
    path_part: str = source.split("|")[0]

    if not path_part or not Path(path_part).exists():
        location = LayerLocation.NON_FILE
    else:
        try:
            layer_path: Path = Path(path_part).resolve()

            if gpkg_path and layer_path == gpkg_path.resolve():
                location = LayerLocation.IN_PROJECT_GPKG
            elif layer_path.is_relative_to(project_dir):
                location = LayerLocation.IN_PROJECT_FOLDER
            else:
                location = LayerLocation.EXTERNAL
        except (ValueError, RuntimeError):
            # Catches errors from invalid paths or if paths are on different drives
            location = LayerLocation.EXTERNAL

    return location
