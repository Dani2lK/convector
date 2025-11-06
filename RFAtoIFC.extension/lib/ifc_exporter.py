# -*- coding: utf-8 -*-
"""IFC4 exporter with Blender-compatible settings."""

import os
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.IFC import *


class IFCExporter:
    """Handles IFC4 export with optimized settings for Blender."""

    def __init__(self, document):
        """Initialize IFC exporter.

        Args:
            document: Revit document to export
        """
        self.document = document

    def export_to_ifc4(self, output_folder, file_name):
        """Export document to IFC4 format with Blender-compatible settings.

        Args:
            output_folder: Folder path for output IFC file
            file_name: Name of the output file (without extension)

        Returns:
            Tuple: (success: bool, output_path: str, error: str)
        """
        try:
            # Ensure output folder exists
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            # Construct full output path
            output_path = os.path.join(output_folder, file_name + '.ifc')

            # Create IFC export options
            ifc_options = IFCExportOptions()

            # Set IFC version to IFC4
            ifc_options.FileVersion = IFCVersion.IFC4
            ifc_options.WallAndColumnSplitting = False

            # Set 3D view for export (sets DetailLevel.Medium)
            view_id = self._get_3d_view_id()
            if view_id != ElementId.InvalidElementId:
                ifc_options.FilterViewId = view_id

            # ALL SETTINGS VIA AddOption() - Compatible with Revit 2024
            # GEOMETRY & QUALITY
            ifc_options.AddOption("ExportSolidModelRep", "True")
            ifc_options.AddOption("UseActiveViewGeometry", "True")

            # MATERIALS - CRITICAL for Blender
            ifc_options.AddOption("ExportSurfaceStyles", "True")
            ifc_options.AddOption("ExportBaseQuantities", "True")
            ifc_options.AddOption("ExportIFCCommonPropertySets", "True")
            ifc_options.AddOption("ExportInternalRevitPropertySets", "True")

            # STANDARD SETTINGS
            ifc_options.AddOption("ExportBoundingBox", "False")
            ifc_options.AddOption("ExportLinkedFiles", "False")
            ifc_options.AddOption("ExportPartsAsBuildingElements", "False")
            ifc_options.AddOption("ExportRoomsIn3DViews", "False")
            ifc_options.AddOption("ExportSchedules", "False")
            ifc_options.AddOption("ExportUserDefinedPsets", "False")
            ifc_options.AddOption("IncludeSiteElevation", "False")
            ifc_options.AddOption("SpaceBoundaryLevel", "0")
            ifc_options.AddOption("SplitWallsAndColumns", "False")

            # NAMING & REFERENCES
            ifc_options.AddOption("StoreIFCGUID", "True")
            ifc_options.AddOption("UseFamilyAndTypeNameForReference", "True")
            ifc_options.AddOption("UseTypeNameOnlyForIfcType", "False")
            ifc_options.AddOption("UseVisibleRevitNameAsEntityName", "True")

            # VIEW SETTINGS
            ifc_options.AddOption("ExportAnnotations", "False")
            ifc_options.AddOption("ExportRoomsInView", "False")
            ifc_options.AddOption("VisibleElementsOfCurrentView", "True")
            ifc_options.AddOption("Use2DRoomBoundaryForVolume", "False")
            ifc_options.AddOption("Export2DElements", "False")

            # Set the file path
            ifc_options.FileName = output_path

            # Perform the export
            result = self.document.Export(output_folder, file_name + '.ifc', ifc_options)

            if result:
                return (True, output_path, "")
            else:
                return (False, "", "Export failed - Revit returned False")

        except Exception as e:
            error_msg = "IFC Export Error: {}".format(str(e))
            print(error_msg)
            return (False, "", error_msg)

    def _get_3d_view_id(self):
        """Get the first available 3D view ID and set its DetailLevel to Medium.

        Returns:
            ElementId of 3D view or ElementId.InvalidElementId
        """
        try:
            # Find 3D views
            collector = FilteredElementCollector(self.document)
            views_3d = collector.OfClass(View3D).ToElements()

            # Find first non-template 3D view and set detail level
            for view in views_3d:
                if not view.IsTemplate:
                    # Set detail level to Medium for balanced quality
                    try:
                        view.DetailLevel = ViewDetailLevel.Medium
                    except:
                        pass
                    return view.Id

            # If no regular 3D view found, return invalid ID
            return ElementId.InvalidElementId

        except Exception as e:
            print("Error getting 3D view: {}".format(str(e)))
            return ElementId.InvalidElementId

    def activate_3d_view(self):
        """Activate a 3D view in the document with Medium detail level.

        Returns:
            View3D object or None if failed
        """
        try:
            collector = FilteredElementCollector(self.document)
            views_3d = collector.OfClass(View3D).ToElements()

            for view in views_3d:
                if not view.IsTemplate:
                    # Set to Medium detail level for balanced quality
                    try:
                        with Transaction(self.document, "Set Detail Level") as t:
                            t.Start()
                            view.DetailLevel = ViewDetailLevel.Medium
                            t.Commit()
                    except:
                        pass
                    return view

            return None

        except Exception as e:
            print("Error activating 3D view: {}".format(str(e)))
            return None

    @staticmethod
    def get_ifc4_folder_name():
        """Get the standard folder name for IFC4 exports.

        Returns:
            String: 'IFC4'
        """
        return 'IFC4'
