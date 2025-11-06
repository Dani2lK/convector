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
            ifc_options.FilterViewId = self._get_3d_view_id()
            ifc_options.StoreIFCGUID = True

            # Quality-based settings
            if quality == 'fast':
                # FASTEST - minimal export
                ifc_options.ExportBaseQuantities = False
                ifc_options.ExportBoundingBox = False
                ifc_options.ExportIFCCommonPropertySets = False
                ifc_options.ExportInternalRevitPropertySets = False
                ifc_options.ExportLinkedFiles = False
                ifc_options.ExportPartsAsBuildingElements = False
                ifc_options.ExportRoomsIn3DViews = False
                ifc_options.ExportSchedules = False
                ifc_options.ExportSolidModelRep = True
                ifc_options.ExportSurfaceStyles = True  # Keep for Blender
                ifc_options.ExportUserDefinedPsets = False
                ifc_options.IncludeSiteElevation = False
                ifc_options.SpaceBoundaryLevel = 0
                ifc_options.SplitWallsAndColumns = False
                ifc_options.TessellationLevelOfDetail = 0.2  # Very coarse
                ifc_options.UseActiveViewGeometry = False
                ifc_options.UseCoarseTessellation = True  # FAST!
                ifc_options.UseFamilyAndTypeNameForReference = False
                ifc_options.UseTypeNameOnlyForIfcType = True
                ifc_options.UseVisibleRevitNameAsEntityName = True
                ifc_options.WallAndColumnSplitting = False

            elif quality == 'medium':
                # BALANCED - good speed with materials
                ifc_options.ExportBaseQuantities = True
                ifc_options.ExportBoundingBox = False
                ifc_options.ExportIFCCommonPropertySets = False
                ifc_options.ExportInternalRevitPropertySets = False
                ifc_options.ExportLinkedFiles = False
                ifc_options.ExportPartsAsBuildingElements = False
                ifc_options.ExportRoomsIn3DViews = False
                ifc_options.ExportSchedules = False
                ifc_options.ExportSolidModelRep = True
                ifc_options.ExportSurfaceStyles = True
                ifc_options.ExportUserDefinedPsets = False
                ifc_options.IncludeSiteElevation = False
                ifc_options.SpaceBoundaryLevel = 0
                ifc_options.SplitWallsAndColumns = False
                ifc_options.TessellationLevelOfDetail = 0.4  # Medium
                ifc_options.UseActiveViewGeometry = True
                ifc_options.UseCoarseTessellation = False
                ifc_options.UseFamilyAndTypeNameForReference = True
                ifc_options.UseTypeNameOnlyForIfcType = False
                ifc_options.UseVisibleRevitNameAsEntityName = True
                ifc_options.WallAndColumnSplitting = False

            else:  # 'high'
                # QUALITY - best output (slower)
                ifc_options.ExportBaseQuantities = True
                ifc_options.ExportBoundingBox = False
                ifc_options.ExportIFCCommonPropertySets = True
                ifc_options.ExportInternalRevitPropertySets = True
                ifc_options.ExportLinkedFiles = False
                ifc_options.ExportPartsAsBuildingElements = False
                ifc_options.ExportRoomsIn3DViews = False
                ifc_options.ExportSchedules = False
                ifc_options.ExportSolidModelRep = True
                ifc_options.ExportSurfaceStyles = True
                ifc_options.ExportUserDefinedPsets = False
                ifc_options.IncludeSiteElevation = False
                ifc_options.SpaceBoundaryLevel = 0
                ifc_options.SplitWallsAndColumns = False
                ifc_options.TessellationLevelOfDetail = 0.6  # Fine
                ifc_options.UseActiveViewGeometry = True
                ifc_options.UseCoarseTessellation = False
                ifc_options.UseFamilyAndTypeNameForReference = True
                ifc_options.UseTypeNameOnlyForIfcType = False
                ifc_options.UseVisibleRevitNameAsEntityName = True
                ifc_options.WallAndColumnSplitting = False

            # Additional speed optimizations
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

    def _get_3d_view_id(self):
        """Get the first available 3D view ID."""
        try:
            collector = FilteredElementCollector(self.document)
            views_3d = collector.OfClass(View3D).ToElements()

            for view in views_3d:
                if not view.IsTemplate:
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
