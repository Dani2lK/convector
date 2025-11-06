# -*- coding: utf-8 -*-
"""Family analyzer to determine family type and hosting requirements."""

from Autodesk.Revit.DB import *


class FamilyAnalyzer:
    """Analyzes family files to determine their type and requirements."""

    @staticmethod
    def get_family_host_type(family_doc):
        """Determine the host type required for a family.

        Args:
            family_doc: Revit family document

        Returns:
            String: 'wall', 'floor', 'ceiling', 'roof', 'standalone'
        """
        if not family_doc:
            return 'standalone'

        # Get family manager
        family_manager = family_doc.FamilyManager

        # Check if family requires a host
        if not family_manager:
            return 'standalone'

        # Get the family category
        family_category = family_doc.OwnerFamily.FamilyCategory if family_doc.OwnerFamily else None

        if not family_category:
            return 'standalone'

        # Check built-in category
        category_id = family_category.Id.IntegerValue

        # Wall-hosted categories (convert to int for comparison)
        wall_hosted = [
            int(BuiltInCategory.OST_Windows),
            int(BuiltInCategory.OST_Doors),
            int(BuiltInCategory.OST_GenericModel),
            int(BuiltInCategory.OST_ElectricalFixtures),
            int(BuiltInCategory.OST_LightingFixtures),
        ]

        # Floor-hosted categories
        floor_hosted = [
            int(BuiltInCategory.OST_Columns),
            int(BuiltInCategory.OST_StructuralColumns),
            int(BuiltInCategory.OST_Furniture),
            int(BuiltInCategory.OST_PlumbingFixtures),
        ]

        # Ceiling-hosted categories
        ceiling_hosted = [
            int(BuiltInCategory.OST_LightingFixtures),
            int(BuiltInCategory.OST_ElectricalFixtures),
        ]

        # Roof-hosted categories
        roof_hosted = [
            int(BuiltInCategory.OST_GenericModel),
        ]

        # Try to determine from family parameters
        try:
            # Check if family has WorkPlane-Based parameter
            for param in family_manager.Parameters:
                if param.Definition.Name == "Work Plane-Based":
                    # This is a face-based or work plane-based family
                    # Need to check hosting behavior more carefully
                    pass

            # Check the hosting behavior through family type
            collector = FilteredElementCollector(family_doc)
            family_symbols = collector.OfClass(FamilySymbol).ToElements()

            for symbol in family_symbols:
                if hasattr(symbol, 'Family'):
                    family = symbol.Family

                    # Check if it's a wall-hosted family
                    if hasattr(family, 'FamilyPlacementType'):
                        placement_type = family.FamilyPlacementType

                        if placement_type == FamilyPlacementType.OneLevelBased:
                            # Check category for more specific determination
                            if category_id in wall_hosted:
                                return 'wall'
                            elif category_id in floor_hosted:
                                return 'floor'
                            elif category_id in ceiling_hosted:
                                return 'ceiling'
                            else:
                                return 'floor'  # Default for level-based

                        elif placement_type == FamilyPlacementType.OneLevelBasedHosted:
                            # Definitely needs a host
                            if category_id in wall_hosted:
                                return 'wall'
                            elif category_id in floor_hosted:
                                return 'floor'
                            elif category_id in ceiling_hosted:
                                return 'ceiling'
                            else:
                                return 'wall'  # Default for hosted

                        elif placement_type == FamilyPlacementType.TwoLevelsBased:
                            return 'standalone'  # Usually doesn't need specific host

                        elif placement_type == FamilyPlacementType.WorkPlaneBased:
                            # Face-based families
                            if category_id in wall_hosted:
                                return 'wall'
                            elif category_id in ceiling_hosted:
                                return 'ceiling'
                            else:
                                return 'wall'  # Default for face-based

        except Exception as e:
            print("Error analyzing family: {}".format(str(e)))

        # Default to standalone if unable to determine
        return 'standalone'

    @staticmethod
    def is_family_loadable(family_doc):
        """Check if family document is valid and loadable.

        Args:
            family_doc: Revit family document

        Returns:
            Boolean: True if family is loadable, False otherwise
        """
        if not family_doc:
            return False

        try:
            # Check if document has family manager
            if not family_doc.FamilyManager:
                return False

            # Check if document is a family document
            if not family_doc.IsFamilyDocument:
                return False

            return True

        except Exception as e:
            print("Error checking family: {}".format(str(e)))
            return False
