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

            # Set IFC export settings for better Blender compatibility

            # Export base quantities (important for materials and geometry)
            ifc_options.ExportBaseQuantities = True

            # Export bounding box
            ifc_options.ExportBoundingBox = False  # Not needed for visual models

            # Export IFC common property sets
            ifc_options.ExportIFCCommonPropertySets = True

            # Export elements in current view only (3D view)
            ifc_options.FilterViewId = self._get_3d_view_id()

            # Export internal Revit property sets (includes materials info)
            ifc_options.ExportInternalRevitPropertySets = True

            # Export linked files
            ifc_options.ExportLinkedFiles = False

            # Export parts as building elements
            ifc_options.ExportPartsAsBuildingElements = False

            # Export rooms in 3D views
            ifc_options.ExportRoomsIn3DViews = False

            # Export schedules
            ifc_options.ExportSchedules = False

            # Export solid models when possible
            ifc_options.ExportSolidModelRep = True

            # Export surface styles (CRITICAL for materials in Blender!)
            # This ensures materials and colors are exported
            ifc_options.ExportSurfaceStyles = True

            # Export user defined property sets
            ifc_options.ExportUserDefinedPsets = False

            # Include IFCSITE elevation
            ifc_options.IncludeSiteElevation = False

            # Space boundaries
            ifc_options.SpaceBoundaryLevel = 0  # No space boundaries

            # Split walls by building stories
            ifc_options.SplitWallsAndColumns = False

            # Store IFC GUID in file
            ifc_options.StoreIFCGUID = True

            # Tessellation quality - controlled by View's DetailLevel setting
            # Note: In Revit 2024, tessellation properties (TessellationLevelOfDetail,
            # UseCoarseTessellation) don't exist in IFCExportOptions API
            # Quality is controlled by setting DetailLevel in 3D View before export

            # Use active view settings - CRITICAL for using View's DetailLevel
            ifc_options.UseActiveViewGeometry = True

            # Use family and type name for references
            ifc_options.UseFamilyAndTypeNameForReference = True

            # Use type name only for IFC entity
            ifc_options.UseTypeNameOnlyForIfcType = False

            # Use visible Revit name as entity name
            ifc_options.UseVisibleRevitNameAsEntityName = True

            # Wall and column splitting
            ifc_options.WallAndColumnSplitting = False

            # Set the file path
            ifc_options.FileName = output_path

            # Add COBie specific settings if needed
            ifc_options.AddOption("ExportAnnotations", "False")
            ifc_options.AddOption("ExportRoomsInView", "False")

            # Additional options for better material export
            ifc_options.AddOption("VisibleElementsOfCurrentView", "True")
            ifc_options.AddOption("Use2DRoomBoundaryForVolume", "False")
            ifc_options.AddOption("UseFamilyAndTypeNameForReference", "True")
            ifc_options.AddOption("Export2DElements", "False")

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
