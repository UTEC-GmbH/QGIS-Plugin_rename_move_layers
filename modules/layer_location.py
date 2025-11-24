"""Module: layer_location.py

Determine the location of the layer's data source.
"""

import os
import sys
from pathlib import Path

from qgis.core import QgsMapLayer, QgsProject, QgsVectorLayer
from qgis.gui import QgisInterface, QgsLayerTreeViewIndicator

from .constants import LayerLocation
from .general import project_gpkg
from .logs_and_errors import log_debug


def _is_within(child: Path, parent: Path) -> bool:
    """Return True if child path is within parent directory (issue #4, py<3.9)."""
    try:
        child_res: Path = child.resolve(strict=False)
        parent_res: Path = parent.resolve(strict=False)
        common: str = os.path.commonpath([str(child_res), str(parent_res)])
        return common == str(parent_res)
    except Exception:
        return False


def _paths_equal(a: Path, b: Path) -> bool:
    """Robust path equality across platforms and links (issue #4)."""
    try:
        # Prefer samefile when possible
        return a.exists() and b.exists() and a.samefile(b)
    except Exception:
        # Fall back to case-insensitive normalized comparison on Windows
        if sys.platform.startswith("win"):
            return os.path.normcase(str(a.resolve(strict=False))) == os.path.normcase(
                str(b.resolve(strict=False))
            )
        return str(a.resolve(strict=False)) == str(b.resolve(strict=False))


def get_layer_location(project: QgsProject, layer: QgsMapLayer) -> LayerLocation | None:
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
    log_debug(f"Location Indicators → '{layer.name()}' → Checking location...")

    if not project.fileName():
        log_debug("Project file name could not be found.")
        return None

    # Check if the layer is empty
    if isinstance(layer, QgsVectorLayer) and layer.featureCount() == 0:
        log_debug(f"Location Indicators → '{layer.name()}' → Layer is empty.")
        return LayerLocation.EMPTY

    # Check if the layer is a memory layer
    # (temporary layers get an indicator from QGIS itself)
    source: str = layer.source()
    if source.startswith("memory"):
        log_debug(
            f"Location Indicators → '{layer.name()}' → "
            "memory layer - no indicator needed."
        )
        return None

    # Check if the layer is a cloud source
    if "url=" in source:
        log_debug(f"Location Indicators → '{layer.name()}' → cloud data source.")
        return LayerLocation.CLOUD

    # Check if the layer is stored in the project folder
    if path_part := source.split("|")[0]:
        project_dir: Path = Path(project.fileName()).parent.resolve()
        gpkg_path: Path = project_gpkg()
        layer_path: Path = Path(path_part).resolve(strict=False)

        # Check if the layer is stored in the project GeoPackage
        if _paths_equal(layer_path, gpkg_path):
            location = LayerLocation.GPKG_PROJECT

        # Check if the layer is stored within the project folder
        elif _is_within(layer_path, project_dir):
            location = (
                LayerLocation.GPKG_FOLDER
                if ".gpkg" in layer_path.name
                else LayerLocation.FOLDER_NO_GPKG
            )
        else:
            location = LayerLocation.EXTERNAL

        log_debug(f"Location Indicators → '{layer.name()}' → location: {location.name}")
        return location

    return None


def add_location_indicator(
    project: QgsProject, iface: QgisInterface, layer: QgsMapLayer
) -> QgsLayerTreeViewIndicator | None:
    """Add a location indicator for a single layer to the layer tree view."""

    location: LayerLocation | None = get_layer_location(project, layer)
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
