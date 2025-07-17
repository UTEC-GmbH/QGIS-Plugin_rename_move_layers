"""This module contains the functions concerning GeoPackages."""

from pathlib import Path

from qgis.core import Qgis, QgsProject
from qgis.gui import QgisInterface


def find_project_gpkg(plugin: QgisInterface) -> Path | None:
    """Check if a GeoPackage with the same name as the project
    exists in the project folder.

    Example: for a project 'my_project.qgz',
    it looks for 'my_project.gpkg' in the same directory.

    :returns: The Path object to the GeoPackage if it exists, otherwise None.
    """
    project: QgsProject | None = QgsProject.instance()
    if project is None:
        plugin.iface.messageBar().pushMessage(
            "Error", "No QGIS project is currently open.", level=Qgis.Critical
        )
        return None

    project_path_str: str = project.fileName()

    project_path: Path = Path(project_path_str)
    gpkg_path: Path = project_path.with_suffix(".gpkg")

    return gpkg_path if gpkg_path.is_file() else None
