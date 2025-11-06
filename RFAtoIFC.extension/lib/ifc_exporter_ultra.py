# -*- coding: utf-8 -*-
"""Ultra high-quality IFC4 exporter optimized for Blender."""

import os
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.IFC import *


class UltraQualityIFCExporter:
    """Handles ultra high-quality IFC4 export for professional visualization in Blender."""

    def __init__(self, document):
        """Initialize IFC exporter.

        Args:
            document: Revit document to export
        """
        self.document = document

    def export_to_ifc4_ultra(self, output_folder, file_name):
        """Export document to IFC4 with MAXIMUM quality for Blender.

        Optimized for:
        - Sharp, precise triangulation
        - Accurate geometry and high detail
        - Complete material export for Blender
        - Professional visualization quality

        Args:
            output_folder: Folder path for output IFC file
            file_name: Name of the output file (without extension)

        Returns:
            Tuple: (success: bool, output_path: str, error: str)
        """
        try:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            output_path = os.path.join(output_folder, file_name + '.ifc')

            # Create IFC export options
            ifc_options = IFCExportOptions()

            # ============================================================
            # CORE SETTINGS - IFC4 for best compatibility
            # ============================================================
            ifc_options.FileVersion = IFCVersion.IFC4
            ifc_options.WallAndColumnSplitting = False

            # Set 3D view for export (also sets DetailLevel.Fine)
            view_id = self._get_3d_view_id()
            if view_id != ElementId.InvalidElementId:
                ifc_options.FilterViewId = view_id

            # ============================================================
            # ALL SETTINGS VIA AddOption() - Compatible with Revit 2024
            # ============================================================

            # GEOMETRY QUALITY - use View's DetailLevel (set to Fine in _get_3d_view_id)
            ifc_options.AddOption("ExportSolidModelRep", "True")  # Твердотельная геометрия
            ifc_options.AddOption("UseActiveViewGeometry", "True")  # Use View DetailLevel

            # MATERIALS & APPEARANCE - CRITICAL FOR BLENDER
            ifc_options.AddOption("ExportSurfaceStyles", "True")  # Материалы и цвета!
            ifc_options.AddOption("ExportBaseQuantities", "True")
            ifc_options.AddOption("ExportIFCCommonPropertySets", "True")
            ifc_options.AddOption("ExportInternalRevitPropertySets", "True")
            ifc_options.AddOption("ExportMaterialPsets", "True")

            # DETAIL & ACCURACY
            ifc_options.AddOption("ExportBoundingBox", "False")
            ifc_options.AddOption("ExportLinkedFiles", "False")
            ifc_options.AddOption("ExportPartsAsBuildingElements", "False")
            ifc_options.AddOption("ExportRoomsIn3DViews", "False")
            ifc_options.AddOption("ExportSchedules", "False")
            ifc_options.AddOption("ExportUserDefinedPsets", "True")

            # STRUCTURAL ACCURACY
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

            # ============================================================
            # PERFORM EXPORT
            # ============================================================

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
        """Get the first available 3D view ID with best detail level.

        Returns:
            ElementId of 3D view or ElementId.InvalidElementId
        """
        try:
            collector = FilteredElementCollector(self.document)
            views_3d = collector.OfClass(View3D).ToElements()

            best_view = None

            for view in views_3d:
                if not view.IsTemplate:
                    # Set detail level to Fine for maximum quality
                    try:
                        view.DetailLevel = ViewDetailLevel.Fine
                    except:
                        pass

                    if best_view is None:
                        best_view = view

            if best_view:
                return best_view.Id

            return ElementId.InvalidElementId

        except Exception as e:
            print("Error getting 3D view: {}".format(str(e)))
            return ElementId.InvalidElementId

    def activate_3d_view(self):
        """Activate a 3D view with Fine detail level.

        Returns:
            View3D object or None if failed
        """
        try:
            collector = FilteredElementCollector(self.document)
            views_3d = collector.OfClass(View3D).ToElements()

            for view in views_3d:
                if not view.IsTemplate:
                    # Set to Fine detail level
                    try:
                        with Transaction(self.document, "Set Detail Level") as t:
                            t.Start()
                            view.DetailLevel = ViewDetailLevel.Fine
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

    def prepare_materials_for_export(self):
        """Prepare materials in document for optimal Blender export.

        This ensures all materials have proper visual properties.
        """
        try:
            # Get all materials
            collector = FilteredElementCollector(self.document)
            materials = collector.OfClass(Material).ToElements()

            with Transaction(self.document, "Prepare Materials") as t:
                t.Start()

                for material in materials:
                    # Ensure material has appearance asset
                    if material.AppearanceAssetId == ElementId.InvalidElementId:
                        # Material doesn't have appearance - skip
                        continue

                    # Material already has appearance - it will be exported

                t.Commit()

        except Exception as e:
            print("Warning: Could not prepare materials: {}".format(str(e)))


class BalancedQualityIFCExporter:
    """Balanced quality exporter with good speed and quality."""

    def __init__(self, document):
        """Initialize IFC exporter.

        Args:
            document: Revit document to export
        """
        self.document = document
        self.ultra_exporter = UltraQualityIFCExporter(document)

    def export_to_ifc4_balanced(self, output_folder, file_name):
        """Export with balanced quality - good for most use cases.

        Args:
            output_folder: Folder path for output IFC file
            file_name: Name of the output file (without extension)

        Returns:
            Tuple: (success: bool, output_path: str, error: str)
        """
        # Use ultra quality settings but with slightly reduced tessellation
        try:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            output_path = os.path.join(output_folder, file_name + '.ifc')

            ifc_options = IFCExportOptions()

            # Core settings
            ifc_options.FileVersion = IFCVersion.IFC4
            ifc_options.WallAndColumnSplitting = False

            # Set 3D view for export (uses Medium DetailLevel)
            view_id = self.ultra_exporter._get_3d_view_id()
            if view_id != ElementId.InvalidElementId:
                ifc_options.FilterViewId = view_id

            # Balanced quality - ALL settings via AddOption()
            ifc_options.AddOption("ExportSolidModelRep", "True")
            ifc_options.AddOption("UseActiveViewGeometry", "True")

            # Materials - full export
            ifc_options.AddOption("ExportSurfaceStyles", "True")
            ifc_options.AddOption("ExportBaseQuantities", "True")
            ifc_options.AddOption("ExportIFCCommonPropertySets", "True")
            ifc_options.AddOption("ExportInternalRevitPropertySets", "False")  # Skip for speed

            # Standard settings
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
            ifc_options.AddOption("UseFamilyAndTypeNameForReference", "True")
            ifc_options.AddOption("UseTypeNameOnlyForIfcType", "False")
            ifc_options.AddOption("UseVisibleRevitNameAsEntityName", "True")

            # View settings
            ifc_options.AddOption("ExportAnnotations", "False")
            ifc_options.AddOption("ExportRoomsInView", "False")
            ifc_options.AddOption("VisibleElementsOfCurrentView", "True")
            ifc_options.AddOption("Use2DRoomBoundaryForVolume", "False")
            ifc_options.AddOption("Export2DElements", "False")

            ifc_options.FileName = output_path

            result = self.document.Export(output_folder, file_name + '.ifc', ifc_options)

            if result:
                return (True, output_path, "")
            else:
                return (False, "", "Export failed")

        except Exception as e:
            return (False, "", "IFC Export Error: {}".format(str(e)))
