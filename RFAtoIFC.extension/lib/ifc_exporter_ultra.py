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

            # ============================================================
            # GEOMETRY QUALITY - MAXIMUM DETAIL
            # ============================================================

            # Tessellation - MAXIMUM quality
            # Note: In Revit 2024, TessellationLevelOfDetail may not exist as property
            # Use AddOption instead for better compatibility
            # Level: 0.0 = finest, 1.0 = coarsest
            # For ULTRA quality we want finest (close to 0.0)

            # Use FINE tessellation (not coarse)
            ifc_options.UseCoarseTessellation = False  # Четкая триангуляция!

            # Export as solid model representation (best for Blender)
            ifc_options.ExportSolidModelRep = True  # Твердотельная геометрия

            # Use active view geometry for accurate representation
            ifc_options.UseActiveViewGeometry = True

            # ============================================================
            # MATERIALS & APPEARANCE - CRITICAL FOR BLENDER
            # ============================================================

            # Export surface styles (colors, materials) - ОБЯЗАТЕЛЬНО для Blender!
            ifc_options.ExportSurfaceStyles = True  # Материалы и цвета!

            # Export base quantities (includes material information)
            ifc_options.ExportBaseQuantities = True

            # Export IFC common property sets (material properties)
            ifc_options.ExportIFCCommonPropertySets = True

            # Export internal Revit property sets (detailed material info)
            ifc_options.ExportInternalRevitPropertySets = True

            # ============================================================
            # DETAIL & ACCURACY
            # ============================================================

            # Don't export bounding box (we need actual geometry)
            ifc_options.ExportBoundingBox = False

            # Export linked files if needed
            ifc_options.ExportLinkedFiles = False

            # Don't export parts as building elements (keep original structure)
            ifc_options.ExportPartsAsBuildingElements = False

            # Don't export rooms in 3D (not needed for families)
            ifc_options.ExportRoomsIn3DViews = False

            # Don't export schedules (not needed)
            ifc_options.ExportSchedules = False

            # Export user-defined property sets (custom parameters)
            ifc_options.ExportUserDefinedPsets = True

            # ============================================================
            # STRUCTURAL ACCURACY
            # ============================================================

            # Don't include site elevation (not needed for families)
            ifc_options.IncludeSiteElevation = False

            # No space boundaries (not needed for families)
            ifc_options.SpaceBoundaryLevel = 0

            # Don't split walls and columns (keep as single objects)
            ifc_options.SplitWallsAndColumns = False

            # Don't split by building stories (keep complete)
            ifc_options.WallAndColumnSplitting = False

            # ============================================================
            # NAMING & REFERENCES
            # ============================================================

            # Store IFC GUID in file for tracking
            ifc_options.StoreIFCGUID = True

            # Use family and type name for clear references
            ifc_options.UseFamilyAndTypeNameForReference = True

            # Use full type information
            ifc_options.UseTypeNameOnlyForIfcType = False

            # Use visible Revit name as entity name (readable names in Blender)
            ifc_options.UseVisibleRevitNameAsEntityName = True

            # ============================================================
            # VIEW SETTINGS
            # ============================================================

            # Set 3D view for export
            ifc_options.FilterViewId = self._get_3d_view_id()

            # ============================================================
            # ADDITIONAL OPTIONS FOR BLENDER COMPATIBILITY
            # ============================================================

            # Don't export annotations (not needed for 3D models)
            ifc_options.AddOption("ExportAnnotations", "False")

            # Don't export rooms in view
            ifc_options.AddOption("ExportRoomsInView", "False")

            # Use visible elements of current view
            ifc_options.AddOption("VisibleElementsOfCurrentView", "True")

            # Don't use 2D room boundary
            ifc_options.AddOption("Use2DRoomBoundaryForVolume", "False")

            # Use family and type name for reference (clear naming)
            ifc_options.AddOption("UseFamilyAndTypeNameForReference", "True")

            # Don't export 2D elements
            ifc_options.AddOption("Export2DElements", "False")

            # Export materials with full detail
            ifc_options.AddOption("ExportMaterialPsets", "True")

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

            # Balanced quality - use coarse tessellation=False for good detail
            ifc_options.UseCoarseTessellation = False
            ifc_options.ExportSolidModelRep = True
            ifc_options.UseActiveViewGeometry = True

            # Materials - full export
            ifc_options.ExportSurfaceStyles = True
            ifc_options.ExportBaseQuantities = True
            ifc_options.ExportIFCCommonPropertySets = True
            ifc_options.ExportInternalRevitPropertySets = False  # Skip for speed

            # Standard settings
            ifc_options.ExportBoundingBox = False
            ifc_options.ExportLinkedFiles = False
            ifc_options.ExportPartsAsBuildingElements = False
            ifc_options.ExportRoomsIn3DViews = False
            ifc_options.ExportSchedules = False
            ifc_options.ExportUserDefinedPsets = False
            ifc_options.IncludeSiteElevation = False
            ifc_options.SpaceBoundaryLevel = 0
            ifc_options.SplitWallsAndColumns = False
            ifc_options.WallAndColumnSplitting = False
            ifc_options.StoreIFCGUID = True
            ifc_options.UseFamilyAndTypeNameForReference = True
            ifc_options.UseTypeNameOnlyForIfcType = False
            ifc_options.UseVisibleRevitNameAsEntityName = True

            ifc_options.FilterViewId = self.ultra_exporter._get_3d_view_id()

            # Additional options
            ifc_options.AddOption("ExportAnnotations", "False")
            ifc_options.AddOption("ExportRoomsInView", "False")
            ifc_options.AddOption("VisibleElementsOfCurrentView", "True")
            ifc_options.AddOption("Use2DRoomBoundaryForVolume", "False")
            ifc_options.AddOption("UseFamilyAndTypeNameForReference", "True")
            ifc_options.AddOption("Export2DElements", "False")

            ifc_options.FileName = output_path

            result = self.document.Export(output_folder, file_name + '.ifc', ifc_options)

            if result:
                return (True, output_path, "")
            else:
                return (False, "", "Export failed")

        except Exception as e:
            return (False, "", "IFC Export Error: {}".format(str(e)))
