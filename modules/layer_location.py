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
    relative to the QGIS project file. It can identify if a layer is stored in
    the project's associated GeoPackage, within the project folder, at an
    external file path, or from a cloud-based service. It also handles special
    cases like memory layers and empty vector layers.

    Args:
        layer (QgsMapLayer): The QGIS map layer to check.

    Returns:
        LayerLocation | None: An enum member indicating the data source location,
        or None for memory layers.
    """
    location: LayerLocation | None = None
    log_message: str = ""

    layer_source: str = os.path.normcase(layer.source())
    gpkg_path: Path = project_gpkg()
    gpkg: str = os.path.normcase(str(gpkg_path))
    project_folder: str = os.path.normcase(str(gpkg_path.parent))

    if isinstance(layer, QgsVectorLayer) and layer.featureCount() == 0:
        location = LayerLocation.EMPTY
        log_message = "Layer is empty."
    elif layer_source.startswith("memory"):
        # Memory layers get an indicator from QGIS itself, so we return None.
        location = None
        log_message = "memory layer - QGIS indicator."
    elif "url=" in layer_source:
        location = LayerLocation.CLOUD
        log_message = "cloud data source."
    elif gpkg in layer_source:
        location = LayerLocation.GPKG_PROJECT
        log_message = "in project GeoPackage. ✅"
    elif project_folder in layer_source:
        if ".gpkg" in layer_source:
            location = LayerLocation.GPKG_FOLDER
            log_message = "in a GeoPackage in the project folder."
        else:
            location = LayerLocation.FOLDER_NO_GPKG
            log_message = "in the project folder, but not in a GeoPackage."
    else:
        location = LayerLocation.EXTERNAL
        log_message = "💥 external data source 💥"

    log_debug(f"Location Indicators → '{layer.name()}' → {log_message}")
    return location


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
