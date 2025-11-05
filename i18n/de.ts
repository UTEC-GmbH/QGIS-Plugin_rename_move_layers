<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="de_DE" sourcelanguage="en">
<context>
    <name>Menu_main</name>
    <message>
        <location filename="../rename_move_layers.py" line="198"/>
        <source>Rename Layers by Group</source>
        <translation>Layer gemäß Gruppe umbenennen</translation>
    </message>
    <message>
        <location filename="../rename_move_layers.py" line="236"/>
        <source>Move Layers to GeoPackage</source>
        <translation>Layer in GeoPackage verschieben</translation>
    </message>
    <message>
        <location filename="../rename_move_layers.py" line="217"/>
        <source>Undo Last Rename</source>
        <translation>Letzte Umbenennung rückgängig machen</translation>
    </message>
    <message>
        <location filename="../rename_move_layers.py" line="255"/>
        <source>Rename and Move Layers to GeoPackage</source>
        <translation>Layer umbenennen und in GeoPackage verschieben</translation>
    </message>
</context>
<context>
    <name>Menu_tip</name>
    <message>
        <location filename="../rename_move_layers.py" line="199"/>
        <source>Rename selected layers to their parent group names</source>
        <translation>Gewählte Layer gemäß ihrer Gruppe umbenennen</translation>
    </message>
    <message>
        <location filename="../rename_move_layers.py" line="237"/>
        <source>Move selected layers to the project&apos;s GeoPackage</source>
        <translation>Gewählte Layer in das Projekt-GeoPackage verschieben</translation>
    </message>
    <message>
        <location filename="../rename_move_layers.py" line="218"/>
        <source>Reverts the last layer renaming operation</source>
        <translation>Macht die letzte Umbenunnung rückgängig</translation>
    </message>
    <message>
        <location filename="../rename_move_layers.py" line="256"/>
        <source>Rename and move selected layers to the project&apos;s GeoPackage</source>
        <translation>Ausgewählte Layer umbenennen und in das GeoPackage des Projektes verschieben</translation>
    </message>
</context>
<context>
    <name>Menu_whats</name>
    <message>
        <location filename="../rename_move_layers.py" line="200"/>
        <source>Renames selected layers to match their parent group&apos;s name.</source>
        <translation>Gewählte Layer werden gemäß ihrer Gruppe umbenannt.</translation>
    </message>
    <message>
        <location filename="../rename_move_layers.py" line="219"/>
        <source>Undoes the most recent layer renaming operation performed by this plugin.</source>
        <translation>Die letzte Umbenennung wird rückgängig gemacht.</translation>
    </message>
    <message>
        <location filename="../rename_move_layers.py" line="238"/>
        <source>Copies selected layers to the project&apos;s GeoPackage (a GeoPackage in the project folder with the same name as the project file) and adds them back from the GeoPackage to the layer tree of the project.</source>
        <translation>Kopiert die Ausgewählten Layer in das GeoPackage des Projekts (ein GeoPackage mit dem selben Namen wie die Projektdatei) und fügt sie aus dem GeoPackage in das Projekt ein.</translation>
    </message>
    <message>
        <location filename="../rename_move_layers.py" line="257"/>
        <source>Renames the selected layers to their parent group names, then copies them to the project&apos;s GeoPackage (a GeoPackage in the project folder with the same name as the project file) and adds them back from the GeoPackage to the layer tree of the project.</source>
        <translation>Benennt die gewählten Layer gemäß ihrer Gruppe um, kopiert sie dann in das GeoPackage des Projekts (ein GeoPackage mit dem gleichen Namen wie die Projektdatei) und fügt sie aus dem GeoPackage dem Projekt hinzu.</translation>
    </message>
</context>
<context>
    <name>RuntimeError</name>
    <message>
        <location filename="../rename_move_layers.py" line="189"/>
        <source>Failed to create the plugin menu.</source>
        <translation>Konnte das Plugin-Menu nicht erstellen.</translation>
    </message>
    <message>
        <location filename="../modules/general.py" line="49"/>
        <source>No QGIS project is currently open.</source>
        <translation>Es ist kein QGIS-Projekt geöffnet.</translation>
    </message>
    <message>
        <location filename="../modules/general.py" line="63"/>
        <source>QGIS interface not set.</source>
        <translation>Das OGIS Interface ist nicht gesetzt.</translation>
    </message>
    <message>
        <location filename="../modules/general.py" line="64"/>
        <source>Could not get layer tree view.</source>
        <translation>Konnte den Layer-Baum nicht öffnen.</translation>
    </message>
    <message>
        <location filename="../modules/geopackage.py" line="70"/>
        <source>Failed to create GeoPackage at: {0}</source>
        <translation>Konnte das Geopackage nicht in folgendem Pfad erstellen: {0}</translation>
    </message>
    <message>
        <location filename="../modules/general.py" line="65"/>
        <source>No layers or groups selected.</source>
        <translation>Keine Layer oder Layer-Gruppen ausgewählt.</translation>
    </message>
    <message>
        <location filename="../modules/geopackage.py" line="221"/>
        <source>Could not get layer tree root.</source>
        <translation>Konnte &quot;layer tree root&quot; nicht finden.</translation>
    </message>
</context>
<context>
    <name>UserError</name>
    <message>
        <location filename="../modules/geopackage.py" line="58"/>
        <source>Project is not saved. Please save the project first.</source>
        <translation>Das Projekt ist noch nicht abgespeichert. Bitte erst speichern.</translation>
    </message>
</context>
<context>
    <name>log_summary</name>
    <message>
        <location filename="../modules/logs_and_errors.py" line="137"/>
        <source>{action} {successes} layer(s).</source>
        <translation>{action} {successes} Layer.</translation>
    </message>
    <message>
        <location filename="../modules/logs_and_errors.py" line="143"/>
        <source>Skipped {num_skipped} layer(s).</source>
        <translation>{num_skipped} Layer übersprungen.</translation>
    </message>
    <message>
        <location filename="../modules/logs_and_errors.py" line="152"/>
        <source>Failed to {action} {num_failures} layer(s).</source>
        <translation>Aktion '{action}' {num_failures} x fehlgeschlagen.</translation>
    </message>
    <message>
        <location filename="../modules/logs_and_errors.py" line="161"/>
        <source>Could not find {len_not_found} layer(s).</source>
        <translation>Konnte {len_not_found} Layer nicht finden.</translation>
    </message>
    <message>
        <location filename="../modules/logs_and_errors.py" line="170"/>
        <source>No layers processed or all selected layers already have the desired state.</source>
        <translation>Es wurden keine Layer bearbeitet oder alle gewählten Layer sind schon im richtigen Zustand.</translation>
    </message>
</context>
</TS>
