# -*- coding: utf-8 -*-
"""Main script for converting RFA files to IFC4 format."""

import sys
import os
import clr
import time

# Add references
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Windows.Forms')

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from System.Windows.Forms import (
    MessageBox, MessageBoxButtons, MessageBoxIcon, DialogResult, Application
)

# Add lib folder to path
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
lib_path = os.path.join(script_dir, 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

from config_manager import ConfigManager
from family_analyzer import FamilyAnalyzer
from ifc_exporter_ultra import UltraQualityIFCExporter
from ui_helpers import (
    FileSelectionHelper, TemplateConfigDialog,
    RevitActivitySimulator, AutoDismissFailureHandler
)


class RFAtoIFCConverter:
    """Main converter class for RFA to IFC4 conversion."""

    def __init__(self, uiapp):
        """Initialize converter.

        Args:
            uiapp: Revit UIApplication
        """
        self.uiapp = uiapp
        self.app = uiapp.Application
        self.config_manager = ConfigManager()
        self.activity_simulator = RevitActivitySimulator(uiapp)
        self.failure_handler = AutoDismissFailureHandler()

        # Statistics
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        self.errors = []

    def run(self):
        """Main entry point for conversion process."""
        try:
            print("\n" + "="*60)
            print("RFA to IFC4 Converter - ULTRA QUALITY")
            print("Максимальное качество для Blender")
            print("="*60 + "\n")

            # Check if templates are configured
            if not self.config_manager.is_configured():
                print("Шаблоны проектов не настроены!")
                result = MessageBox.Show(
                    "Необходимо настроить пути к шаблонам проектов.\n\n"
                    "Открыть настройки сейчас?",
                    "Настройка шаблонов",
                    MessageBoxButtons.YesNo,
                    MessageBoxIcon.Question
                )

                if result == DialogResult.Yes:
                    dialog = TemplateConfigDialog(self.config_manager)
                    Application.Run(dialog)

                    if dialog.result != DialogResult.OK:
                        print("Настройка отменена. Выход.")
                        return
                else:
                    print("Выход.")
                    return

            # Select RFA file(s)
            last_rfa_folder = self.config_manager.get_last_rfa_folder()
            rfa_path, is_folder = FileSelectionHelper.select_rfa_file_or_folder(
                last_rfa_folder
            )

            if not rfa_path:
                print("Выбор файлов отменен.")
                return

            # Get list of RFA files to process
            rfa_files = self._get_rfa_files(rfa_path, is_folder)

            if not rfa_files:
                MessageBox.Show(
                    "Не найдено файлов .rfa для конвертации.",
                    "Ошибка",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                )
                return

            print("Найдено файлов для обработки: {}".format(len(rfa_files)))

            # Save last RFA folder
            if is_folder:
                self.config_manager.set_last_rfa_folder(rfa_path)
            else:
                self.config_manager.set_last_rfa_folder(os.path.dirname(rfa_path))

            # Select export folder
            last_export_folder = self.config_manager.get_last_export_folder()
            export_folder = FileSelectionHelper.select_export_folder(last_export_folder)

            if not export_folder:
                print("Выбор папки экспорта отменен.")
                return

            # Save last export folder
            self.config_manager.set_last_export_folder(export_folder)

            # Create IFC4 subfolder
            ifc4_folder = os.path.join(export_folder, UltraQualityIFCExporter.get_ifc4_folder_name())
            if not os.path.exists(ifc4_folder):
                os.makedirs(ifc4_folder)

            print("\nПапка экспорта: {}".format(ifc4_folder))
            print("\nНачинаем конвертацию...\n")

            # Start activity simulation
            self.activity_simulator.start()

            # Process each RFA file
            self.total_files = len(rfa_files)
            for i, rfa_file in enumerate(rfa_files, 1):
                print("-" * 60)
                print("[{}/{}] Обработка: {}".format(
                    i, self.total_files, os.path.basename(rfa_file)
                ))
                self._process_rfa_file(rfa_file, ifc4_folder)

            # Stop activity simulation
            self.activity_simulator.stop()

            # Show summary
            self._show_summary()

        except Exception as e:
            print("\nКритическая ошибка: {}".format(str(e)))
            import traceback
            traceback.print_exc()

            # Stop activity simulator
            if hasattr(self, 'activity_simulator'):
                self.activity_simulator.stop()

            MessageBox.Show(
                "Произошла ошибка:\n\n{}".format(str(e)),
                "Ошибка",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )

    def _get_rfa_files(self, path, is_folder):
        """Get list of RFA files to process.

        Args:
            path: File or folder path
            is_folder: True if path is folder, False if file

        Returns:
            List of RFA file paths
        """
        if is_folder:
            rfa_files = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith('.rfa'):
                        rfa_files.append(os.path.join(root, file))
            return sorted(rfa_files)
        else:
            return [path] if path.lower().endswith('.rfa') else []

    def _process_rfa_file(self, rfa_file_path, output_folder):
        """Process single RFA file.

        Args:
            rfa_file_path: Path to RFA file
            output_folder: Output folder for IFC file
        """
        family_doc = None
        project_doc = None

        try:
            # Open family document
            print("  Открытие файла семейства...")
            family_doc = self.app.OpenDocumentFile(rfa_file_path)

            if not family_doc or not family_doc.IsFamilyDocument:
                raise Exception("Не удалось открыть файл как семейство Revit")

            # Analyze family type
            print("  Определение типа семейства...")
            family_type = FamilyAnalyzer.get_family_host_type(family_doc)
            print("  Тип семейства: {}".format(family_type))

            # Get appropriate template
            template_path = self.config_manager.get_template_path(family_type)
            if not template_path or not os.path.exists(template_path):
                raise Exception("Шаблон проекта для типа '{}' не найден".format(family_type))

            print("  Загрузка шаблона проекта...")
            project_doc = self.app.OpenDocumentFile(template_path)

            if not project_doc:
                raise Exception("Не удалось открыть шаблон проекта")

            # Load family into project with transaction
            print("  Загрузка семейства в проект...")
            loaded_family = None

            with Transaction(project_doc, "Load Family") as t:
                # Set failure handler
                options = t.GetFailureHandlingOptions()
                options.SetFailuresPreprocessor(self.failure_handler)
                t.SetFailureHandlingOptions(options)

                t.Start()

                try:
                    # Load family
                    success = family_doc.LoadFamily(project_doc, TransactionFamilyLoadOptions())

                    if not success:
                        print("  Предупреждение: LoadFamily вернул False, но продолжаем...")

                    # Find loaded family
                    collector = FilteredElementCollector(project_doc)
                    families = collector.OfClass(Family).ToElements()

                    family_name = os.path.splitext(os.path.basename(rfa_file_path))[0]

                    for fam in families:
                        if fam.Name == family_name:
                            loaded_family = fam
                            break

                    t.Commit()

                except Exception as e:
                    t.RollBack()
                    raise Exception("Ошибка загрузки семейства: {}".format(str(e)))

            if not loaded_family:
                # Try to find by partial name match
                collector = FilteredElementCollector(project_doc)
                families = collector.OfClass(Family).ToElements()
                if len(families) > 0:
                    loaded_family = families[0]  # Take first family
                    print("  Найдено семейство: {}".format(loaded_family.Name))

            # Place family instance on 3D view
            print("  Размещение семейства в проекте...")
            self._place_family_instance(project_doc, loaded_family, family_type)

            # Get 3D view and activate it
            print("  Активация 3D вида...")
            exporter = UltraQualityIFCExporter(project_doc)
            view_3d = exporter.activate_3d_view()

            if not view_3d:
                print("  Предупреждение: 3D вид не найден, но продолжаем экспорт...")

            # Export to IFC4 with ULTRA quality
            print("  Экспорт в IFC4 (максимальное качество)...")
            file_name = os.path.splitext(os.path.basename(rfa_file_path))[0]
            success, output_path, error = exporter.export_to_ifc4_ultra(output_folder, file_name)

            if success:
                print("  ✓ Успешно экспортировано: {}".format(output_path))
                self.successful += 1
            else:
                raise Exception("Ошибка экспорта: {}".format(error))

        except Exception as e:
            error_msg = "Ошибка обработки '{}': {}".format(
                os.path.basename(rfa_file_path), str(e)
            )
            print("  ✗ {}".format(error_msg))
            self.errors.append(error_msg)
            self.failed += 1

        finally:
            # Close documents
            try:
                if project_doc and not project_doc.IsLinked:
                    project_doc.Close(False)
            except:
                pass

            try:
                if family_doc and not family_doc.IsLinked:
                    family_doc.Close(False)
            except:
                pass

    def _place_family_instance(self, doc, family, family_type):
        """Place family instance in project.

        Args:
            doc: Project document
            family: Loaded family
            family_type: Type of family ('wall', 'floor', 'ceiling', 'roof', 'standalone')
        """
        if not family:
            return

        with Transaction(doc, "Place Family") as t:
            # Set failure handler
            options = t.GetFailureHandlingOptions()
            options.SetFailuresPreprocessor(self.failure_handler)
            t.SetFailureHandlingOptions(options)

            t.Start()

            try:
                # Get first family symbol
                symbol_ids = family.GetFamilySymbolIds()
                if symbol_ids.Count == 0:
                    t.Commit()
                    return

                symbol_id = list(symbol_ids)[0]
                symbol = doc.GetElement(symbol_id)

                if not symbol:
                    t.Commit()
                    return

                # Activate symbol if not active
                if not symbol.IsActive:
                    symbol.Activate()
                    doc.Regenerate()

                # Place instance based on family type
                if family_type == 'wall':
                    self._place_on_wall(doc, symbol)
                elif family_type == 'floor':
                    self._place_on_floor(doc, symbol)
                elif family_type == 'ceiling':
                    self._place_on_ceiling(doc, symbol)
                elif family_type == 'roof':
                    self._place_on_roof(doc, symbol)
                else:  # standalone
                    self._place_standalone(doc, symbol)

                t.Commit()

            except Exception as e:
                t.RollBack()
                print("  Предупреждение при размещении: {}".format(str(e)))

    def _place_on_wall(self, doc, symbol):
        """Place family instance on wall."""
        # Find first wall
        collector = FilteredElementCollector(doc)
        walls = collector.OfClass(Wall).ToElements()

        if len(walls) > 0:
            wall = walls[0]

            # Get wall location curve
            location = wall.Location
            if isinstance(location, LocationCurve):
                curve = location.Curve
                point = curve.Evaluate(0.5, True)  # Mid-point

                # Create instance
                try:
                    instance = doc.Create.NewFamilyInstance(
                        point, symbol, wall, doc.GetElement(wall.LevelId),
                        StructuralType.NonStructural
                    )
                except:
                    # Try without host
                    instance = doc.Create.NewFamilyInstance(
                        point, symbol, StructuralType.NonStructural
                    )

    def _place_on_floor(self, doc, symbol):
        """Place family instance on floor."""
        # Find first floor
        collector = FilteredElementCollector(doc)
        floors = collector.OfClass(Floor).ToElements()

        if len(floors) > 0:
            floor = floors[0]

            # Get floor center point
            bbox = floor.get_BoundingBox(None)
            if bbox:
                center = (bbox.Min + bbox.Max) * 0.5

                # Create instance
                try:
                    level = doc.GetElement(floor.LevelId)
                    instance = doc.Create.NewFamilyInstance(
                        center, symbol, floor, level,
                        StructuralType.NonStructural
                    )
                except:
                    # Try without host
                    instance = doc.Create.NewFamilyInstance(
                        center, symbol, StructuralType.NonStructural
                    )
        else:
            # Place at origin if no floor
            self._place_standalone(doc, symbol)

    def _place_on_ceiling(self, doc, symbol):
        """Place family instance on ceiling."""
        # Find first ceiling
        collector = FilteredElementCollector(doc)
        ceilings = collector.OfClass(Ceiling).ToElements()

        if len(ceilings) > 0:
            ceiling = ceilings[0]

            # Get ceiling center point
            bbox = ceiling.get_BoundingBox(None)
            if bbox:
                center = (bbox.Min + bbox.Max) * 0.5

                # Create instance
                try:
                    level = doc.GetElement(ceiling.LevelId)
                    instance = doc.Create.NewFamilyInstance(
                        center, symbol, ceiling, level,
                        StructuralType.NonStructural
                    )
                except:
                    # Try face-based placement
                    self._place_standalone(doc, symbol)
        else:
            # Place at origin if no ceiling
            self._place_standalone(doc, symbol)

    def _place_on_roof(self, doc, symbol):
        """Place family instance on roof."""
        # Find first roof
        collector = FilteredElementCollector(doc)
        roofs = collector.OfClass(RoofBase).ToElements()

        if len(roofs) > 0:
            roof = roofs[0]

            # Get roof center point
            bbox = roof.get_BoundingBox(None)
            if bbox:
                center = (bbox.Min + bbox.Max) * 0.5

                # Create instance
                try:
                    level = doc.GetElement(roof.LevelId)
                    instance = doc.Create.NewFamilyInstance(
                        center, symbol, roof, level,
                        StructuralType.NonStructural
                    )
                except:
                    # Try without host
                    self._place_standalone(doc, symbol)
        else:
            # Place at origin if no roof
            self._place_standalone(doc, symbol)

    def _place_standalone(self, doc, symbol):
        """Place standalone family instance."""
        # Place at origin
        origin = XYZ(0, 0, 0)

        # Get first level
        collector = FilteredElementCollector(doc)
        levels = collector.OfClass(Level).ToElements()

        if len(levels) > 0:
            level = levels[0]
            try:
                instance = doc.Create.NewFamilyInstance(
                    origin, symbol, level, StructuralType.NonStructural
                )
            except:
                # Try without level
                try:
                    instance = doc.Create.NewFamilyInstance(
                        origin, symbol, StructuralType.NonStructural
                    )
                except Exception as e:
                    print("    Не удалось разместить: {}".format(str(e)))

    def _show_summary(self):
        """Show conversion summary."""
        print("\n" + "="*60)
        print("ИТОГИ КОНВЕРТАЦИИ")
        print("="*60)
        print("Всего файлов: {}".format(self.total_files))
        print("Успешно: {}".format(self.successful))
        print("Ошибок: {}".format(self.failed))

        if self.errors:
            print("\nОшибки:")
            for error in self.errors:
                print("  - {}".format(error))

        print("="*60 + "\n")

        # Show message box
        if self.failed == 0:
            MessageBox.Show(
                "Конвертация завершена успешно!\n\n"
                "Обработано файлов: {}".format(self.total_files),
                "Готово",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
        else:
            MessageBox.Show(
                "Конвертация завершена с ошибками.\n\n"
                "Успешно: {}\n"
                "Ошибок: {}\n\n"
                "Подробности смотрите в консоли.".format(
                    self.successful, self.failed
                ),
                "Готово",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )


class TransactionFamilyLoadOptions(IFamilyLoadOptions):
    """Custom family load options to handle overwrites."""

    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        """Handle family found event."""
        overwriteParameterValues = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        """Handle shared family found event."""
        overwriteParameterValues = True
        return True


def main():
    """Main entry point."""
    try:
        # Get Revit application
        uiapp = __revit__

        # Create and run converter
        converter = RFAtoIFCConverter(uiapp)
        converter.run()

    except Exception as e:
        print("Ошибка: {}".format(str(e)))
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
