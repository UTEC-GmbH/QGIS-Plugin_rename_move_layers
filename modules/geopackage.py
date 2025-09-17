"""Module: functions_geopackage.py

This module contains the functions concerning GeoPackages.
"""

import re
from pathlib import Path

from osgeo import ogr
from qgis.core import (
    Qgis,
    QgsLayerTree,
    QgsMapLayer,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import (
    QCoreApplication,  # type: ignore[reportAttributeAccessIssue]
)

from .general import (
    EMPTY_LAYER_NAME,
    GEOMETRY_SUFFIX_MAP,
    clear_attribute_table,
    get_current_project,
    get_selected_layers,
    raise_runtime_error,
)
from .logs_and_errors import log_debug, log_summary_message
from .rename import geometry_type_suffix


def project_gpkg() -> Path:
    """Check if a GeoPackage with the same name as the project
    exists in the project folder and creates it if not.

    Example: for a project 'my_project.qgz',
    it looks for 'my_project.gpkg' in the same directory.

    :returns: The Path object to the GeoPackage.
    :raises RuntimeError: If the project is not saved.
    :raises IOError: If the GeoPackage file cannot be created.
    """
    project: QgsProject = get_current_project()
    project_path_str: str = project.fileName()
    if not project_path_str:
        raise_runtime_error(
            QCoreApplication.translate(
                "RuntimeError", "Project is not saved. Please save the project first."
            )
        )

    project_path: Path = Path(project_path_str)
    gpkg_path: Path = project_path.with_suffix(".gpkg")

    if not gpkg_path.exists():
        driver = ogr.GetDriverByName("GPKG")
        data_source = driver.CreateDataSource(str(gpkg_path))
        if data_source is None:
            raise_runtime_error(
                QCoreApplication.translate(
                    "RuntimeError", "Failed to create GeoPackage at: {0}"
                ).format(gpkg_path)
            )

        # Dereference the data source to close the file and release the lock.
        data_source = None

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


def add_layers_to_gpkg() -> None:
    """Add the selected layers to the project's GeoPackage."""

    project: QgsProject = get_current_project()
    layers: list[QgsMapLayer] = get_selected_layers()
    gpkg_path: Path = project_gpkg()

    results: dict = {"successes": 0, "failures": []}

    for layer in layers:
        if isinstance(layer, QgsVectorLayer) and layer.name() != EMPTY_LAYER_NAME:
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = check_existing_layer(gpkg_path, layer)
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, str(gpkg_path), project.transformContext(), options
            )
            if error[0] == QgsVectorFileWriter.WriterError.NoError:
                results["successes"] += 1

                # Load the new layer from the GeoPackage to clear its attributes
                # (the attributes that are imported fom AutoCAD are useless)
                uri: str = f"{gpkg_path}|layername={layer.name()}"
                gpkg_layer = QgsVectorLayer(uri, layer.name(), "ogr")
                if gpkg_layer.isValid():
                    clear_attribute_table(gpkg_layer)
                else:
                    log_debug(
                        QCoreApplication.translate(
                            "GeoPackage",
                            "Could not reload layer '{0}' from GeoPackage "
                            "to clear attributes.",
                        ).format(layer.name()),
                        Qgis.Warning,
                    )

            else:
                results["failures"].append((layer.name(), error[1]))

    log_summary_message(
        successes=results["successes"],
        failures=results["failures"],
        action="Added to GeoPackage",
    )


def add_layers_from_gpkg_to_project() -> None:
    """Add the selected layers from the project's GeoPackage."""
    project: QgsProject = get_current_project()
    selected_layers: list[QgsMapLayer] = get_selected_layers()
    gpkg_path: Path = project_gpkg()
    gpkg_path_str = str(gpkg_path)

    root: QgsLayerTree | None = project.layerTreeRoot()
    if not root:
        raise_runtime_error(
            QCoreApplication.translate("RuntimeError", "Could not get layer tree view.")
        )

    added_layers: list[str] = []
    not_found_layers: list[str] = []

    for layer_to_find in selected_layers:
        layer_name: str = layer_to_find.name()

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

    if added_layers:
        log_debug(
            QCoreApplication.translate(
                "log", "Added '{0}' layer(s) from the GeoPackage to the project."
            ).format(len(added_layers)),
            Qgis.Success,
        )
    if not_found_layers:
        log_debug(
            QCoreApplication.translate(
                "log",
                "Could not find {count} layer(s) in GeoPackage: {layer_list}",
            ).format(
                count=len(not_found_layers), layer_list=", ".join(not_found_layers)
            ),
            Qgis.Warning,
        )

    log_summary_message(
        successes=len(added_layers),
        failures=not_found_layers,
        action="Added from GeoPackage",
    )


def move_layers_to_gpkg() -> None:
    """Move the selected layers to the project's GeoPackage."""

    add_layers_to_gpkg()
    add_layers_from_gpkg_to_project()
