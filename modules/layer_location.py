"""Module: layer_location.py

Determine the location of the layer's data source.
"""

import os
import sys
from pathlib import Path

from qgis.core import QgsMapLayer, QgsProject
from qgis.gui import QgisInterface, QgsLayerTreeViewIndicator

from .constants import LayerLocation
from .general import get_current_project, project_gpkg
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


def get_layer_location(layer: QgsMapLayer) -> LayerLocation:
    """Determine the location of the layer's data source with caching.

    Args:
        layer: The QGIS map layer to check.

    Returns:
        A LayerLocation enum member indicating the layer's data source location.
    """

    log_debug(f"Checking location of layer '{layer.name()}'...")

    project: QgsProject = get_current_project()
    if not project.fileName():
        log_debug("Prject file name could not be found.")
        return LayerLocation.UNKNOWN

    project_dir: Path = Path(project.fileName()).parent.resolve()
    gpkg_path: Path = project_gpkg()

    source: str = layer.source()
    if path_part := source.split("|")[0]:
        p = Path(path_part)
        try:
            layer_path: Path = p.resolve(strict=False)
            if _paths_equal(layer_path, gpkg_path):
                location = LayerLocation.IN_PROJECT_GPKG
            elif _is_within(layer_path, project_dir):
                location = LayerLocation.IN_PROJECT_FOLDER
            else:
                location = LayerLocation.EXTERNAL
        except Exception:
            # Catches errors from invalid paths or if paths are on different drives
            location = LayerLocation.EXTERNAL

    else:
        location = LayerLocation.NON_FILE

    log_debug(f"Layer '{layer.name()}': {location.tooltip}")
    return location


def add_location_indicator(
    iface: QgisInterface, layer: QgsMapLayer
) -> QgsLayerTreeViewIndicator | None:
    """Add a location indicator for a single layer to the layer tree view."""

    location: LayerLocation = get_layer_location(layer)
    indicator = QgsLayerTreeViewIndicator()
    indicator.setIcon(location.icon)
    indicator.setToolTip(location.tooltip)
    if (
        (project := QgsProject().instance())
        and (view := iface.layerTreeView())
        and (root := project.layerTreeRoot())
        and (node := root.findLayer(layer.id()))
    ):
        view.addIndicator(node, indicator)
        log_debug(f"Layer '{layer.name()}': {indicator.toolTip()}")
        return indicator

    return None
