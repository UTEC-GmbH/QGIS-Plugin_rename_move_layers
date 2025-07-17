"""Module: functions_geopackage.py

This module contains the functions concerning GeoPackages.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from osgeo import ogr
from qgis.core import (
    Qgis,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
)
from qgis.gui import QgisInterface

from .functions_general import get_current_project, get_selected_layers

if TYPE_CHECKING:
    from qgis.core import QgsMapLayer


def project_gpkg(plugin: QgisInterface) -> Path:
    """Check if a GeoPackage with the same name as the project
    exists in the project folder and creates it if not.

    Example: for a project 'my_project.qgz',
    it looks for 'my_project.gpkg' in the same directory.

    :returns: The Path object to the GeoPackage.
    :raises RuntimeError: If the project is not saved.
    :raises IOError: If the GeoPackage file cannot be created.
    """
    project: QgsProject = get_current_project(plugin)
    project_path_str: str = project.fileName()
    if not project_path_str:
        error_msg: str = "Project is not saved. Please save the project first."
        plugin.iface.messageBar().pushMessage(
            "Error", error_msg, level=Qgis.Critical, duration=5
        )
        raise RuntimeError(error_msg)

    project_path: Path = Path(project_path_str)
    gpkg_path: Path = project_path.with_suffix(".gpkg")

    if not gpkg_path.exists():
        driver = ogr.GetDriverByName("GPKG")
        gpkg_path = driver.CreateDataSource(str(gpkg_path))

    return gpkg_path


def add_layers_to_gpkg(plugin: QgisInterface) -> None:
    """Add the selected layers to the project's GeoPackage."""

    project: QgsProject = get_current_project(plugin)
    layers: list[QgsMapLayer] = get_selected_layers(plugin)
    gpkg_path: Path = project_gpkg(plugin)
    gpkg_path_str = str(gpkg_path)

    results: dict = {"successes": 0, "failures": []}

    for layer in layers:
        if isinstance(layer, QgsVectorLayer):
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = layer.name()
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

            error: tuple = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, gpkg_path_str, project.transformContext(), options
            )
            if error[0] == QgsVectorFileWriter.WriterError.NoError:
                results["successes"] += 1
            else:
                results["failures"].append((layer.name(), error[1]))

    if results["successes"] > 0:
        plugin.iface.messageBar().pushMessage(
            "Success",
            f"Copied {results['successes']} layers to GeoPackage.",
            level=Qgis.Success,
        )
    if results["failures"]:
        for layer_name, error_msg in results["failures"]:
            plugin.iface.messageBar().pushMessage(
                "Error",
                f"Failed to copy layer '{layer_name}': {error_msg}",
                level=Qgis.Critical,
            )


def move_layers_to_gpkg(plugin: QgisInterface) -> None:
    """Move the selected layers to the project's GeoPackage."""

    add_layers_to_gpkg(plugin)
