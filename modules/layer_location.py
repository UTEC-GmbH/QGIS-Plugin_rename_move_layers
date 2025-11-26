"""Module: layer_location.py

Determine the location of the layer's data source.
"""

import os
from typing import TYPE_CHECKING

from qgis.core import QgsMapLayer, QgsProject, QgsVectorLayer
from qgis.gui import QgisInterface, QgsLayerTreeViewIndicator

from .constants import LayerLocation
from .general import project_gpkg
from .logs_and_errors import log_debug

if TYPE_CHECKING:
    from pathlib import Path


def get_layer_location(layer: QgsMapLayer) -> LayerLocation | None:
    """Determine the location of the layer's data source.

    This function analyzes the layer's source string to classify its location
    relative to the QGIS project file. It can identify if a layer is stored
    in the project's associated GeoPackage, within the project folder, at an
    external file path, or from a cloud-based service. It also handles special
    cases like memory layers and empty vector layers.

    Args:
        project: The current QGIS project instance.
        layer: The QGIS map layer to check.

    Returns:
        A LayerLocation enum member indicating the layer's data source location,
        or None if no indicator should be shown (e.g., for memory layers or if
        the project is not saved).
    """
    layer_source: str = os.path.normcase(layer.source())
    gpkg_path: Path = project_gpkg()
    gpkg: str = os.path.normcase(str(gpkg_path))
    project_folder: str = os.path.normcase(str(gpkg_path.parent))
    log_debug(
        f"Location Indicators → '{layer.name()}' → Checking location...\n"
        f"Layer Source: {layer_source}\n"
        f"Project GeoPackage: {gpkg}\n"
        f"Project Folder: {project_folder}"
    )

    # Check if the layer is empty
    if isinstance(layer, QgsVectorLayer) and layer.featureCount() == 0:
        log_debug(f"Location Indicators → '{layer.name()}' → Layer is empty.")
        return LayerLocation.EMPTY

    # Check if the layer is a memory layer
    # (temporary layers get an indicator from QGIS itself)
    if layer_source.startswith("memory"):
        log_debug(
            f"Location Indicators → '{layer.name()}' → memory layer - QGIS indicator."
        )
        return None

    # Check if the layer is a cloud source
    if "url=" in layer_source:
        log_debug(f"Location Indicators → '{layer.name()}' → cloud data source.")
        return LayerLocation.CLOUD

    # Check if the layer is in the project GeoPackage
    if gpkg in layer_source:
        log_debug(f"Location Indicators → '{layer.name()}' → in project GeoPackage.")
        return LayerLocation.GPKG_PROJECT

    # Check if the layer is stored in the project folder
    if project_folder in layer_source:
        # Check if the layer is stored in a GeoPackage (not the project GeoPackage)
        if ".gpkg" in layer_source:
            log_debug(
                f"Location Indicators → '{layer.name()}' → "
                "in a GeoPackage in the project folder."
            )
            return LayerLocation.GPKG_FOLDER

        log_debug(
            f"Location Indicators → '{layer.name()}' → "
            "in the project folder, but not in a GeoPackage."
        )
        return LayerLocation.FOLDER_NO_GPKG

    log_debug(f"Location Indicators → '{layer.name()}' → !!! external data source !!!")
    return LayerLocation.EXTERNAL


def add_location_indicator(
    project: QgsProject, iface: QgisInterface, layer: QgsMapLayer
) -> QgsLayerTreeViewIndicator | None:
    """Add a location indicator for a single layer to the layer tree view."""

    location: LayerLocation | None = get_layer_location(layer)
    if location is None:
        return None

    indicator = QgsLayerTreeViewIndicator()
    indicator.setIcon(location.icon)
    indicator.setToolTip(location.tooltip)
    if (
        project
        and (view := iface.layerTreeView())
        and (root := project.layerTreeRoot())
        and (node := root.findLayer(layer.id()))
    ):
        view.addIndicator(node, indicator)
        log_debug(f"Location Indicators → '{layer.name()}' → adding indicator...")
        return indicator

    return None
