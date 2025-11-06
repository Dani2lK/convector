# -*- coding: utf-8 -*-
"""Fast IFC4 exporter with optimized settings for speed."""

import os
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.IFC import *


class FastIFCExporter:
    """Handles fast IFC4 export with reduced detail for speed."""

    def __init__(self, document):
        """Initialize IFC exporter.

        Args:
            document: Revit document to export
        """
        self.document = document

    def export_to_ifc4_fast(self, output_folder, file_name, quality='medium'):
        """Export document to IFC4 with optimized settings for speed.

        Args:
            output_folder: Folder path for output IFC file
            file_name: Name of the output file (without extension)
            quality: Export quality - 'fast', 'medium', 'high'

        Returns:
            Tuple: (success: bool, output_path: str, error: str)
        """
        try:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            output_path = os.path.join(output_folder, file_name + '.ifc')

            # Create IFC export options
            ifc_options = IFCExportOptions()

            # Basic settings
            ifc_options.FileVersion = IFCVersion.IFC4
            ifc_options.WallAndColumnSplitting = False

            # Set 3D view with appropriate DetailLevel
            view_id = self._get_3d_view_id(quality)
            if view_id != ElementId.InvalidElementId:
                ifc_options.FilterViewId = view_id

            # ALL SETTINGS VIA AddOption() - Compatible with Revit 2024
            # Quality-based settings
            if quality == 'fast':
                # FASTEST - minimal export, uses Coarse DetailLevel from view
                ifc_options.AddOption("ExportSolidModelRep", "True")
                ifc_options.AddOption("ExportSurfaceStyles", "True")  # Keep for Blender
                ifc_options.AddOption("ExportBaseQuantities", "False")
                ifc_options.AddOption("ExportIFCCommonPropertySets", "False")
                ifc_options.AddOption("ExportInternalRevitPropertySets", "False")
                ifc_options.AddOption("UseActiveViewGeometry", "False")
                ifc_options.AddOption("UseFamilyAndTypeNameForReference", "False")
                ifc_options.AddOption("UseTypeNameOnlyForIfcType", "True")

            elif quality == 'medium':
                # BALANCED - good speed with materials, uses Medium DetailLevel
                ifc_options.AddOption("ExportSolidModelRep", "True")
                ifc_options.AddOption("ExportSurfaceStyles", "True")
                ifc_options.AddOption("ExportBaseQuantities", "True")
                ifc_options.AddOption("ExportIFCCommonPropertySets", "False")
                ifc_options.AddOption("ExportInternalRevitPropertySets", "False")
                ifc_options.AddOption("UseActiveViewGeometry", "True")
                ifc_options.AddOption("UseFamilyAndTypeNameForReference", "True")
                ifc_options.AddOption("UseTypeNameOnlyForIfcType", "False")

            else:  # 'high'
                # QUALITY - best output, uses Fine DetailLevel
                ifc_options.AddOption("ExportSolidModelRep", "True")
                ifc_options.AddOption("ExportSurfaceStyles", "True")
                ifc_options.AddOption("ExportBaseQuantities", "True")
                ifc_options.AddOption("ExportIFCCommonPropertySets", "True")
                ifc_options.AddOption("ExportInternalRevitPropertySets", "True")
                ifc_options.AddOption("UseActiveViewGeometry", "True")
                ifc_options.AddOption("UseFamilyAndTypeNameForReference", "True")
                ifc_options.AddOption("UseTypeNameOnlyForIfcType", "False")

            # Common settings for all quality modes
            ifc_options.AddOption("ExportBoundingBox", "False")
            ifc_options.AddOption("ExportLinkedFiles", "False")
            ifc_options.AddOption("ExportPartsAsBuildingElements", "False")
            ifc_options.AddOption("ExportRoomsIn3DViews", "False")
            ifc_options.AddOption("ExportSchedules", "False")
            ifc_options.AddOption("ExportUserDefinedPsets", "False")
            ifc_options.AddOption("IncludeSiteElevation", "False")
            ifc_options.AddOption("SpaceBoundaryLevel", "0")
            ifc_options.AddOption("SplitWallsAndColumns", "False")
            ifc_options.AddOption("StoreIFCGUID", "True")
            ifc_options.AddOption("UseVisibleRevitNameAsEntityName", "True")
            ifc_options.AddOption("ExportAnnotations", "False")
            ifc_options.AddOption("ExportRoomsInView", "False")
            ifc_options.AddOption("Export2DElements", "False")

            ifc_options.FileName = output_path

            # Perform export
            result = self.document.Export(output_folder, file_name + '.ifc', ifc_options)

            if result:
                return (True, output_path, "")
            else:
                return (False, "", "Export returned False")

        except Exception as e:
            error_msg = "IFC Export Error: {}".format(str(e))
            return (False, "", error_msg)

    def _get_3d_view_id(self, quality='medium'):
        """Get the first available 3D view ID and set DetailLevel based on quality.

        Args:
            quality: Export quality - 'fast', 'medium', 'high'
        """
        try:
            collector = FilteredElementCollector(self.document)
            views_3d = collector.OfClass(View3D).ToElements()

            # Map quality to DetailLevel
            detail_level_map = {
                'fast': ViewDetailLevel.Coarse,
                'medium': ViewDetailLevel.Medium,
                'high': ViewDetailLevel.Fine
            }
            detail_level = detail_level_map.get(quality, ViewDetailLevel.Medium)

            for view in views_3d:
                if not view.IsTemplate:
                    # Set detail level based on quality setting
                    try:
                        view.DetailLevel = detail_level
                    except:
                        pass
                    return view.Id

            return ElementId.InvalidElementId

        except Exception as e:
            return ElementId.InvalidElementId

    def activate_3d_view(self):
        """Activate a 3D view in the document."""
        try:
            collector = FilteredElementCollector(self.document)
            views_3d = collector.OfClass(View3D).ToElements()

            for view in views_3d:
                if not view.IsTemplate:
                    return view

            return None

        except Exception as e:
            return None

    @staticmethod
    def get_ifc4_folder_name():
        """Get the standard folder name for IFC4 exports."""
        return 'IFC4'
