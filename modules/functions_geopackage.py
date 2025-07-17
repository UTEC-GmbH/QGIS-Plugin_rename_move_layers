"""Module: functions_geopackage.py

This module contains the functions concerning GeoPackages.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from qgis.core import QgsProject, QgsVectorFileWriter, QgsWkbTypes
from qgis.gui import QgisInterface

from .functions_general import check_project, get_selected_layers

if TYPE_CHECKING:
    from qgis.core import QgsMapLayer


def project_gpkg(plugin: QgisInterface) -> Path:
    """Check if a GeoPackage with the same name as the project
    exists in the project folder and creates it if not.

    Example: for a project 'my_project.qgz',
    it looks for 'my_project.gpkg' in the same directory.

    :returns: The Path object to the GeoPackage if it exists, otherwise None.
    """
    project: QgsProject = check_project(plugin)

    project_path_str: str = project.fileName()

    project_path: Path = Path(project_path_str)
    gpkg_path: Path = project_path.with_suffix(".gpkg")
    gpkg_path.touch()

    return gpkg_path


def copy_layers_to_gpkg(plugin: QgisInterface) -> None:
    """Copy the selected layers to the project's GeoPackage."""

    layers: list[QgsMapLayer] = get_selected_layers(plugin)
    gpkg_path: Path = project_gpkg(plugin)
    gpkg_path_str = str(gpkg_path)

    # Initialize success and failure lists to track results
    successes = 0
    failures = []

    for layer in layers:
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.writeGeometryType = QgsWkbTypes.Unknown
        options.overrideGeometryType = True
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        error = QgsVectorFileWriter.writeAsVectorFormat(layer, gpkg_path_str, options)
        if error[0] == QgsVectorFileWriter.NoError:
            successes += 1
        else:
            failures.append(
                (layer.name(), error[1])
            )  # Store layer name and error message
