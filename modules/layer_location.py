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
        child_res = child.resolve(strict=False)
        parent_res = parent.resolve(strict=False)
        common = os.path.commonpath([str(child_res), str(parent_res)])
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
    log_debug(f"Checking location of layer '{layer.name()}'...")

    if not project.fileName():
        log_debug("Project file name could not be found.")
        return None

    # Only check feature count for vector layers to avoid performance issues
    # and incorrect identification of raster layers as empty.
    if isinstance(layer, QgsVectorLayer) and layer.featureCount() == 0:
        log_debug(f"Layer '{layer.name()}' is an empty vector layer.")
        return LayerLocation.EMPTY

    source: str = layer.source()
    if source.startswith("memory"):
        log_debug(f"Layer '{layer.name()}' is a memory layer. No indicator needed.")
        return None

    if "url=" in source:
        log_debug(f"Layer '{layer.name()}': Cloud data source.")
        return LayerLocation.CLOUD

    if path_part := source.split("|")[0]:
        project_dir: Path = Path(project.fileName()).parent.resolve()
        gpkg_path: Path = project_gpkg()
        layer_path: Path = Path(path_part).resolve(strict=False)
        if _paths_equal(layer_path, gpkg_path):
            location = LayerLocation.IN_PROJECT_GPKG
        elif _is_within(layer_path, project_dir):
            location = LayerLocation.IN_PROJECT_FOLDER
        else:
            location = LayerLocation.EXTERNAL

        log_debug(f"Layer '{layer.name()}': {location.tooltip}")
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
        log_debug(f"Layer '{layer.name()}': {indicator.toolTip()}")
        return indicator

    return None
