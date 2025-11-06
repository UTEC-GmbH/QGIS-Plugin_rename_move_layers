"""Module: functions_geopackage.py

This module contains the functions concerning GeoPackages.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING

from osgeo import ogr
from qgis.core import (
    Qgis,
    QgsLayerTree,
    QgsMapLayer,
    QgsProject,
    QgsVectorDataProvider,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import (
    QCoreApplication,  # type: ignore[reportAttributeAccessIssue]
)

from .constants import EMPTY_LAYER_NAME, GEOMETRY_SUFFIX_MAP
from .general import get_current_project, get_selected_layers
from .logs_and_errors import (
    log_debug,
    log_summary_message,
    raise_runtime_error,
    raise_user_error,
)
from .rename import geometry_type_suffix

if TYPE_CHECKING:
    from qgis.core import (
        QgsDataProvider,
        QgsMapLayerStyle,
        QgsMapLayerStyleManager,
    )


def project_gpkg() -> Path:
    """Check if a GeoPackage with the same name as the project
    exists in the project folder and creates it if not.

    Example: for a project 'my_project.qgz',
    it looks for 'my_project.gpkg' in the same directory.

    :returns: The Path object to the GeoPackage.
    :raises UserError: If the project is not saved.
    :raises IOError: If the GeoPackage file cannot be created.
    """
    project: QgsProject = get_current_project()
    project_path_str: str = project.fileName()
    if not project_path_str:
        # fmt: off
        msg: str = QCoreApplication.translate("UserError", "Project is not saved. Please save the project first.")  # noqa: E501
        # fmt: on
        raise_user_error(msg)

    project_path: Path = Path(project_path_str)
    gpkg_path: Path = project_path.with_suffix(".gpkg")

    if not gpkg_path.exists():
        driver = ogr.GetDriverByName("GPKG")
        data_source = driver.CreateDataSource(str(gpkg_path))
        if data_source is None:
            # fmt: off
            msg: str = QCoreApplication.translate("RuntimeError", "Failed to create GeoPackage at: {0}").format(gpkg_path)  # noqa: E501
            # fmt: on
            raise_runtime_error(msg)

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


def clear_attribute_table(layer: "QgsMapLayer") -> None:
    """Clear the attribute table of a QGIS layer by deleting all columns.

    Args:
        layer: The layer whose attribute table should be cleared.
    """
    if not isinstance(layer, QgsVectorLayer):
        # This function only applies to vector layers.
        return

    provider: QgsDataProvider | None = layer.dataProvider()
    if not provider:
        return

    # Check if the provider supports deleting attributes.
    if not provider.capabilities() & QgsVectorDataProvider.DeleteAttributes:
        return

    if field_indices := list(range(layer.fields().count())):
        provider.deleteAttributes(field_indices)
        layer.updateFields()


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

            error: tuple = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, str(gpkg_path), project.transformContext(), options
            )
            if error[0] == QgsVectorFileWriter.WriterError.NoError:
                results["successes"] += 1

                # Load the new layer from the GeoPackage
                uri: str = f"{gpkg_path}|layername={options.layerName}"
                gpkg_layer = QgsVectorLayer(uri, options.layerName, "ogr")
                if gpkg_layer.isValid() and isinstance(layer, QgsVectorLayer):
                    is_autocad_import: bool = all(
                        s in layer.source().lower()
                        for s in ["|subset=layer", " and space=", " and block="]
                    )
                    if is_autocad_import:
                        clear_attribute_table(gpkg_layer)
                else:
                    log_debug(
                        f"Could not reload layer '{layer.name()}' from GeoPackage."
                    )

            else:
                results["failures"].append((layer.name(), error[1]))

    log_summary_message(
        successes=results["successes"],
        failures=results["failures"],
        action="Added to GeoPackage",
    )


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


def add_layers_from_gpkg_to_project() -> None:
    """Add the selected layers from the project's GeoPackage."""
    project: QgsProject = get_current_project()
    selected_layers: list[QgsMapLayer] = get_selected_layers()
    gpkg_path: Path = project_gpkg()
    gpkg_path_str = str(gpkg_path)

    root: QgsLayerTree | None = project.layerTreeRoot()
    if not root:
        # fmt: off
        msg: str = QCoreApplication.translate("RuntimeError", "Could not get layer tree root.")  # noqa: E501
        # fmt: on
        raise_runtime_error(msg)

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

        # Copy the layer's style to the GeoPackage layer
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

    add_layers_to_gpkg()
    add_layers_from_gpkg_to_project()
