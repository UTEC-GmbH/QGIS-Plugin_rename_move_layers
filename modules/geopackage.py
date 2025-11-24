"""Module: functions_geopackage.py

This module contains the functions concerning GeoPackages.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING

import processing
from osgeo import ogr
from qgis.core import (
    Qgis,
    QgsLayerTree,
    QgsMapLayer,
    QgsProject,
    QgsRasterLayer,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QCoreApplication

from .constants import GEOMETRY_SUFFIX_MAP
from .general import (
    clear_attribute_table,
    get_current_project,
    get_selected_layers,
    project_gpkg,
)
from .logs_and_errors import (
    log_debug,
    log_summary_message,
    raise_runtime_error,
)
from .rename import geometry_type_suffix

if TYPE_CHECKING:
    from qgis.core import QgsMapLayerStyle, QgsMapLayerStyleManager


def create_gpkg(gpkg_path: Path | None = None) -> Path:
    """Check if the GeoPackage exists and create an empty one if not.

    :param gpkg_path: The path to the GeoPackage.
    """

    if gpkg_path is None:
        gpkg_path = project_gpkg()

    if gpkg_path.exists():
        log_debug(f"Existing GeoPackage found in '{gpkg_path}'")
        return gpkg_path

    log_debug(
        f"GeoPackage does not exist yet. Creating empty GeoPackage '{gpkg_path}'..."
    )

    driver = ogr.GetDriverByName("GPKG")
    ds = driver.CreateDataSource(str(gpkg_path))
    if ds is None:
        raise_runtime_error(f"Could not create GeoPackage at '{gpkg_path}'")
    # close datasource to flush file
    ds = None

    return gpkg_path


def check_existing_layer(gpkg_path: Path, layer: QgsMapLayer) -> str:
    """Check if a layer with the same name and geometry type exists in the GeoPackage.

    If a layer with the same name but different geometry type exists, a new
    unique name is returned by appending a geometry suffix. If a layer with
    the same name and geometry type exists, the original name is returned to
    allow overwriting.

    :param gpkg_path: The path to the GeoPackage.
    :param layer: The layer to check for existence.
    :returns: A layer name for the GeoPackage. This will be the original name
              if no layer with that name exists, or if a layer with the same
              name and geometry type exists (allowing overwrite). It will be a
              new name with a suffix if a layer with the same name but
              different geometry type exists.
    """
    if not isinstance(layer, QgsVectorLayer):
        return layer.name()

    layer_name: str = layer.name()
    uri: str = f"{gpkg_path}|layername={layer_name}"
    gpkg_layer = QgsVectorLayer(uri, layer_name, "ogr")

    if not gpkg_layer.isValid():
        # Layer does not exist, safe to use original name.
        return layer_name

    # A layer with the same name exists. Check geometry types.
    incoming_geom_type: Qgis.GeometryType = QgsWkbTypes.geometryType(layer.wkbType())
    existing_geom_type: Qgis.GeometryType = QgsWkbTypes.geometryType(
        gpkg_layer.wkbType()
    )

    if incoming_geom_type == existing_geom_type:
        # Name and geometry match, so we can overwrite. Return original name.
        return layer_name

    # Name matches but geometry is different. Create a new name with a suffix.
    # First, strip any existing geometry suffix from the layer name to get a
    # base name to prevent creating names with double suffixes (e.g., 'layer-pt-pt').
    suffix_values: str = "|".join(GEOMETRY_SUFFIX_MAP.values())
    suffix_pattern: str = rf"\s-\s({suffix_values})$"
    base_name: str = re.sub(suffix_pattern, "", layer_name)

    return f"{base_name}{geometry_type_suffix(layer)}"


def add_vector_layer_to_gpkg(
    project: QgsProject, layer: QgsMapLayer, gpkg_path: Path
) -> tuple:
    """Add a vector layer to the GeoPackage.

    :param layer: The layer to add.
    :param gpkg_path: The path to the GeoPackage.
    """

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = check_existing_layer(gpkg_path, layer)
    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

    return QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, str(gpkg_path), project.transformContext(), options
    )


def add_raster_layer_to_gpkg(layer: QgsMapLayer, gpkg_path: Path) -> dict:
    """Add a raster layer to the GeoPackage using gdal:warpreproject.

    This function uses `gdal:warpreproject` as it can handle various raster
    sources, including file-based rasters and web services (like XYZ tiles),
    and correctly adds them to a GeoPackage.

    :param layer: The layer to add.
    :param gpkg_path: The path to the GeoPackage.
    """
    layer_name: str = check_existing_layer(gpkg_path, layer)
    params: dict = {
        "INPUT": layer,
        "SOURCE_CRS": layer.crs(),
        "TARGET_CRS": layer.crs(),
        "OUTPUT": str(gpkg_path),
        "OPTIONS": f"APPEND_SUBDATASET=YES,RASTER_TABLE={layer_name},"
        "RASTER_TABLE_OPTIONS=OVERWRITE=YES",
    }

    return processing.run("gdal:warpreproject", params)


def clear_autocad_attributes(layer: QgsMapLayer, gpkg_path: Path) -> None:
    """Clear all AutoCAD attributes from a layer's attribute table.

    :param layer: The layer to clear AutoCAD attributes from.
    """

    uri: str = f"{gpkg_path}|layername={layer.name()}"
    gpkg_layer = QgsVectorLayer(uri, layer.name(), "ogr")
    if gpkg_layer.isValid() and isinstance(layer, QgsVectorLayer):
        is_autocad_import: bool = all(
            s in layer.source().lower()
            for s in ["|subset=layer", " and space=", " and block="]
        )
        if is_autocad_import:
            log_debug(
                f"AutoCAD import detected for layer '{layer.name()}'. "
                "Clearing attribute table."
            )
            clear_attribute_table(gpkg_layer)
    else:
        log_debug(f"Could not reload layer '{layer.name()}' from GeoPackage.")


def add_layers_to_gpkg(
    layers: list[QgsMapLayer] | None = None, gpkg_path: Path | None = None
) -> dict:
    """Add the selected layers to the project's GeoPackage.

    :param gpkg_path: Optional path to the GeoPackage. If not provided, the project's
                      default GeoPackage is used.
    :param layers: Optional list of layers to add. If not provided, the currently
                   selected layers are used.
    :returns: A dictionary containing the results of the operation, including
              successes, failures, and a mapping of original layers to their
              names in the GeoPackage.
    """

    project: QgsProject = get_current_project()
    if gpkg_path is None:
        gpkg_path = project_gpkg()

    if not gpkg_path.exists():
        raise_runtime_error(f"GeoPackage does not exist at '{gpkg_path}'")

    results: dict = {"successes": 0, "failures": [], "layer_mapping": {}}
    if layers is None:
        layers = get_selected_layers()
    for layer in layers:
        layer_name: str = check_existing_layer(gpkg_path, layer)
        log_debug(
            f"Adding layer '{layer.name()}' of type '{layer.type()}' "
            f"to GeoPackage {gpkg_path.name}..."
        )

        if isinstance(layer, QgsVectorLayer):
            error: tuple = add_vector_layer_to_gpkg(project, layer, gpkg_path)
            if error[0] == QgsVectorFileWriter.WriterError.NoError:
                results["successes"] += 1
                results["layer_mapping"][layer] = layer_name
                clear_autocad_attributes(layer, gpkg_path)
            else:
                results["failures"].append((layer.name(), error[1]))
                log_debug(f"Failed to add layer '{layer.name()}': {error[1]}")

        elif isinstance(layer, QgsRasterLayer):
            if "url=" in layer.source():
                log_debug(f"Layer '{layer.name()}' is a web service. Skipping.")
                results["successes"] += 1
                results["layer_mapping"][layer] = layer_name
            else:
                raster_results: dict = add_raster_layer_to_gpkg(layer, gpkg_path)
                if raster_results["OUTPUT"]:
                    results["successes"] += 1
                    results["layer_mapping"][layer] = layer_name
                else:
                    results["failures"].append((layer.name(), raster_results["LOG"]))
                    log_debug(
                        f"Failed to add layer '{layer.name()}': {raster_results['LOG']}"
                    )
        else:
            results["failures"].append((layer.name(), "Unsupported layer type."))
            log_debug(f"Failed to add layer '{layer.name()}': Unsupported layer type.")

    log_summary_message(
        successes=results["successes"],
        failures=results["failures"],
        action="Added to GeoPackage",
    )

    return results


def copy_layer_style(source_layer: QgsMapLayer, target_layer: QgsMapLayer) -> None:
    """Copy the active style from a source layer to a target layer.

    This function retrieves the currently active style from the `source_layer`,
    adds it to the `target_layer`'s style manager under the name
    'copied_style', and then sets this new style as the current one for the
    target layer. Finally, it triggers a repaint to ensure the changes are
    visible in the QGIS interface.

    Args:
        source_layer: The QGIS layer from which to copy the style.
        target_layer: The QGIS layer to which the style will be applied.
    """

    mngr_source: QgsMapLayerStyleManager | None = source_layer.styleManager()
    mngr_target: QgsMapLayerStyleManager | None = target_layer.styleManager()

    if mngr_source is None or mngr_target is None:
        return

    # get the name of the source layer's current style
    style_name: str = mngr_source.currentStyle()

    # get the style by the name
    style: QgsMapLayerStyle = mngr_source.style(style_name)

    # add the style to the target layer with a custom name (in this case: 'copied')
    mngr_target.addStyle("copied_style", style)

    # set the added style as the current style
    mngr_target.setCurrentStyle("copied_style")

    # propogate the changes to the QGIS GUI
    target_layer.triggerRepaint()
    target_layer.emitStyleChanged()


def add_layers_from_gpkg_to_project(
    gpkg_path: Path | None = None,
    project: QgsProject | None = None,
    layers: list[QgsMapLayer] | None = None,
    layer_mapping: dict[QgsMapLayer, str] | None = None,
) -> None:
    """Add the selected layers from the project's GeoPackage.

    :param gpkg_path: Optional path to the GeoPackage.
    :param project: Optional project to add layers to.
    :param layers: Optional list of layers to add.
    :param layer_mapping: Optional mapping of original layer objects to their
                          names in the GeoPackage.
    """
    if project is None:
        project = get_current_project()
    if layers is None:
        layers = get_selected_layers()
    if gpkg_path is None:
        gpkg_path = project_gpkg()

    gpkg_path_str = str(gpkg_path)

    root: QgsLayerTree | None = project.layerTreeRoot()
    if not root:
        # fmt: off
        msg: str = QCoreApplication.translate("RuntimeError", "Could not get layer tree root.")  # noqa: E501
        # fmt: on
        raise_runtime_error(msg)

    added_layers: list[str] = []
    not_found_layers: list[str] = []

    for layer_to_find in layers:
        # Determine the layer name in the GPKG (or original name for web layers)
        if layer_mapping and layer_to_find in layer_mapping:
            layer_name: str = layer_mapping[layer_to_find]
        else:
            layer_name = layer_to_find.name()

        # Handle Web Service Layers (skip GPKG lookup, just clone)
        if (
            isinstance(layer_to_find, QgsRasterLayer)
            and "url=" in layer_to_find.source()
        ):
            # Clone the layer to avoid modifying the original
            gpkg_layer = layer_to_find.clone()
            # Ensure the cloned layer has the correct name
            # (it might have been renamed in mapping, though unlikely for web layers)
            gpkg_layer.setName(layer_name)

        # Handle Local Raster Layers (load from GPKG)
        elif isinstance(layer_to_find, QgsRasterLayer):
            uri: str = f"GPKG:{gpkg_path_str}:{layer_name}"
            gpkg_layer = QgsRasterLayer(uri, layer_name, "gdal")

        # Handle Vector Layers (load from GPKG)
        else:
            # Construct the layer URI and create a QgsVectorLayer
            uri: str = f"{gpkg_path_str}|layername={layer_name}"
            gpkg_layer = QgsVectorLayer(uri, layer_name, "ogr")

        if not gpkg_layer.isValid():
            not_found_layers.append(layer_name)
            continue

        # Add the layer to the project registry first, but not the layer tree
        project.addMapLayer(gpkg_layer, addToLegend=False)
        # Then, insert it at the top of the layer tree
        root.insertLayer(0, gpkg_layer)

        added_layers.append(layer_name)

        # Copy the layer's style to the GeoPackage layer
        # (only if it's not a cloned web layer)
        # Web layers already have their style from cloning
        if not (
            "url=" in layer_to_find.source()
            and isinstance(layer_to_find, QgsRasterLayer)
        ):
            copy_layer_style(layer_to_find, gpkg_layer)

    if added_layers:
        log_debug(
            f"Added '{len(added_layers)}' layer(s) from the GeoPackage to the project.",
            Qgis.Success,
        )
    if not_found_layers:
        log_debug(
            f"Could not find {len(not_found_layers)} layer(s) "
            f"in GeoPackage: {', '.join(not_found_layers)}",
            Qgis.Warning,
        )

    log_summary_message(
        successes=len(added_layers),
        failures=not_found_layers,
        action="Added from GeoPackage",
    )


def move_layers_to_gpkg() -> None:
    """Move the selected layers to the project's GeoPackage."""

    results = add_layers_to_gpkg()
    add_layers_from_gpkg_to_project(layer_mapping=results.get("layer_mapping"))
