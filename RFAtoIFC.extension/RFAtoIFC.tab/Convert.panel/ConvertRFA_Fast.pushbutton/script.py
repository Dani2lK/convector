# -*- coding: utf-8 -*-
"""Performance-optimized converter with template caching."""

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


class FastRFAtoIFCConverter:
    """Optimized converter with template caching and batch processing."""

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

        # Template cache - КЛЮЧЕВАЯ ОПТИМИЗАЦИЯ!
        self.template_cache = {}
        self.cache_enabled = True

        # Statistics
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        self.errors = []
        self.start_time = None
        self.performance_stats = {
            'open_family': 0,
            'load_template': 0,
            'load_family': 0,
            'place_instance': 0,
            'export_ifc': 0
        }

    def run(self):
        """Main entry point for conversion process."""
        try:
            print("\n" + "="*60)
            print("RFA to IFC4 Converter (Fast Mode)")
            print("="*60 + "\n")

            # Check configuration
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

            # Get list of RFA files
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

            self.config_manager.set_last_export_folder(export_folder)

            # Create IFC4 subfolder
            ifc4_folder = os.path.join(export_folder, UltraQualityIFCExporter.get_ifc4_folder_name())
            if not os.path.exists(ifc4_folder):
                os.makedirs(ifc4_folder)

            print("\nПапка экспорта: {}".format(ifc4_folder))

            # Ask about optimization mode
            result = MessageBox.Show(
                "Использовать режим ускоренной обработки?\n\n"
                "ДА - быстрее, но использует больше памяти (кэширование шаблонов)\n"
                "НЕТ - медленнее, но меньше памяти",
                "Режим обработки",
                MessageBoxButtons.YesNoCancel,
                MessageBoxIcon.Question
            )

            if result == DialogResult.Cancel:
                print("Отменено пользователем.")
                return

            self.cache_enabled = (result == DialogResult.Yes)

            if self.cache_enabled:
                print("\n✓ Режим: БЫСТРЫЙ (с кэшированием шаблонов)")
                print("  Шаблоны будут загружены один раз и использованы повторно")
            else:
                print("\n✓ Режим: СТАНДАРТНЫЙ")

            print("\nНачинаем конвертацию...\n")

            # Start timer
            self.start_time = time.time()

            # Start activity simulation
            self.activity_simulator.start()

            # Preload templates if caching enabled
            if self.cache_enabled:
                print("Предзагрузка шаблонов...")
                self._preload_templates()
                print("✓ Шаблоны загружены в память\n")

            # Process each RFA file
            self.total_files = len(rfa_files)
            for i, rfa_file in enumerate(rfa_files, 1):
                print("-" * 60)
                print("[{}/{}] Обработка: {}".format(
                    i, self.total_files, os.path.basename(rfa_file)
                ))
                self._process_rfa_file_fast(rfa_file, ifc4_folder)

            # Clean up cache
            if self.cache_enabled:
                print("\nОчистка кэша шаблонов...")
                self._cleanup_cache()

            # Stop activity simulation
            self.activity_simulator.stop()

            # Calculate total time
            total_time = time.time() - self.start_time

            # Show summary
            self._show_summary(total_time)

        except Exception as e:
            print("\nКритическая ошибка: {}".format(str(e)))
            import traceback
            traceback.print_exc()

            # Clean up
            if hasattr(self, 'template_cache'):
                self._cleanup_cache()

            if hasattr(self, 'activity_simulator'):
                self.activity_simulator.stop()

            MessageBox.Show(
                "Произошла ошибка:\n\n{}".format(str(e)),
                "Ошибка",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )

    def _preload_templates(self):
        """Preload all templates into cache."""
        template_types = ['wall', 'floor', 'ceiling', 'roof', 'standalone']

        for template_type in template_types:
            template_path = self.config_manager.get_template_path(template_type)
            if template_path and os.path.exists(template_path):
                try:
                    print("  Загрузка: {}...".format(template_type))
                    doc = self.app.OpenDocumentFile(template_path)
                    if doc:
                        self.template_cache[template_type] = doc
                except Exception as e:
                    print("  ⚠ Ошибка загрузки {}: {}".format(template_type, str(e)))

    def _cleanup_cache(self):
        """Close all cached template documents."""
        for template_type, doc in self.template_cache.items():
            try:
                if doc and not doc.IsLinked:
                    doc.Close(False)
            except:
                pass
        self.template_cache.clear()

    def _get_template_document(self, template_type):
        """Get template document (from cache or load new).

        Args:
            template_type: Type of template

        Returns:
            Document or None
        """
        if self.cache_enabled:
            # Return from cache
            return self.template_cache.get(template_type)
        else:
            # Load new document each time
            template_path = self.config_manager.get_template_path(template_type)
            if template_path and os.path.exists(template_path):
                try:
                    return self.app.OpenDocumentFile(template_path)
                except:
                    return None
            return None

    def _get_rfa_files(self, path, is_folder):
        """Get list of RFA files to process."""
        if is_folder:
            rfa_files = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith('.rfa'):
                        rfa_files.append(os.path.join(root, file))
            return sorted(rfa_files)
        else:
            return [path] if path.lower().endswith('.rfa') else []

    def _process_rfa_file_fast(self, rfa_file_path, output_folder):
        """Process single RFA file with optimizations.

        Args:
            rfa_file_path: Path to RFA file
            output_folder: Output folder for IFC file
        """
        family_doc = None
        project_doc = None
        should_close_project = True  # Only close if not cached

        try:
            # 1. Open family document
            step_start = time.time()
            print("  Открытие семейства...")
            family_doc = self.app.OpenDocumentFile(rfa_file_path)

            if not family_doc or not family_doc.IsFamilyDocument:
                raise Exception("Не удалось открыть файл как семейство Revit")

            self.performance_stats['open_family'] += time.time() - step_start

            # 2. Analyze family type
            step_start = time.time()
            print("  Определение типа...", end=" ")
            family_type = FamilyAnalyzer.get_family_host_type(family_doc)
            print("{}".format(family_type))

            # 3. Get template (cached or new)
            step_start = time.time()
            if self.cache_enabled:
                print("  Использование шаблона из кэша...")
                project_doc = self.template_cache.get(family_type)
                should_close_project = False  # Don't close cached templates
            else:
                print("  Загрузка шаблона...")
                template_path = self.config_manager.get_template_path(family_type)
                if not template_path or not os.path.exists(template_path):
                    raise Exception("Шаблон для '{}' не найден".format(family_type))
                project_doc = self.app.OpenDocumentFile(template_path)

            if not project_doc:
                raise Exception("Не удалось получить шаблон проекта")

            self.performance_stats['load_template'] += time.time() - step_start

            # 4. Load family into project - OPTIMIZED (no transaction needed)
            step_start = time.time()
            print("  Загрузка в проект...")
            loaded_family = None

            try:
                # Load family - creates its own transaction internally
                family_doc.LoadFamily(project_doc, TransactionFamilyLoadOptions())

                # Quick find family (no transaction needed for reading)
                family_name = os.path.splitext(os.path.basename(rfa_file_path))[0]
                collector = FilteredElementCollector(project_doc).OfClass(Family)

                for fam in collector:
                    if fam.Name == family_name:
                        loaded_family = fam
                        break

                if not loaded_family and collector.GetElementCount() > 0:
                    loaded_family = collector.FirstElement()

            except Exception as e:
                raise Exception("Ошибка загрузки: {}".format(str(e)))

            self.performance_stats['load_family'] += time.time() - step_start

            # 5. Place instance - SIMPLIFIED
            step_start = time.time()
            print("  Размещение...")
            self._place_family_simple(project_doc, loaded_family)
            self.performance_stats['place_instance'] += time.time() - step_start

            # 6. Export to IFC4 with ULTRA quality
            step_start = time.time()
            print("  Экспорт IFC4 (максимальное качество)...")
            exporter = UltraQualityIFCExporter(project_doc)
            file_name = os.path.splitext(os.path.basename(rfa_file_path))[0]
            success, output_path, error = exporter.export_to_ifc4_ultra(output_folder, file_name)

            self.performance_stats['export_ifc'] += time.time() - step_start

            if success:
                print("  ✓ Готово: {}".format(os.path.basename(output_path)))
                self.successful += 1
            else:
                raise Exception("Ошибка экспорта: {}".format(error))

        except Exception as e:
            error_msg = "Ошибка '{}': {}".format(
                os.path.basename(rfa_file_path), str(e)
            )
            print("  ✗ {}".format(error_msg))
            self.errors.append(error_msg)
            self.failed += 1

        finally:
            # Close documents
            try:
                if family_doc and not family_doc.IsLinked:
                    family_doc.Close(False)
            except:
                pass

            # Only close project if not cached
            if should_close_project:
                try:
                    if project_doc and not project_doc.IsLinked:
                        project_doc.Close(False)
                except:
                    pass

    def _place_family_simple(self, doc, family):
        """Simplified family placement - just activate symbol.

        Args:
            doc: Project document
            family: Loaded family
        """
        if not family:
            return

        # ОПТИМИЗАЦИЯ: Не размещаем instance, только активируем symbol
        # Это достаточно для экспорта в IFC

        with Transaction(doc, "Activate") as t:
            options = t.GetFailureHandlingOptions()
            options.SetFailuresPreprocessor(self.failure_handler)
            t.SetFailureHandlingOptions(options)

            t.Start()
            try:
                symbol_ids = family.GetFamilySymbolIds()
                if symbol_ids.Count > 0:
                    symbol_id = list(symbol_ids)[0]
                    symbol = doc.GetElement(symbol_id)
                    if symbol and not symbol.IsActive:
                        symbol.Activate()
                t.Commit()
            except:
                t.RollBack()

    def _show_summary(self, total_time):
        """Show conversion summary with performance stats."""
        print("\n" + "="*60)
        print("ИТОГИ КОНВЕРТАЦИИ")
        print("="*60)
        print("Всего файлов: {}".format(self.total_files))
        print("Успешно: {}".format(self.successful))
        print("Ошибок: {}".format(self.failed))
        print("\nВремя работы: {:.1f} сек ({:.1f} мин)".format(
            total_time, total_time / 60.0
        ))

        if self.successful > 0:
            avg_time = total_time / self.total_files
            print("Среднее время на файл: {:.1f} сек".format(avg_time))

        # Performance breakdown
        if self.total_files > 0:
            print("\nРаспределение времени:")
            total_ops = sum(self.performance_stats.values())
            if total_ops > 0:
                for op, time_spent in self.performance_stats.items():
                    pct = (time_spent / total_ops) * 100
                    print("  {}: {:.1f}% ({:.1f}s)".format(op, pct, time_spent))

        if self.errors:
            print("\nОшибки:")
            for error in self.errors[:10]:  # Show first 10
                print("  - {}".format(error))
            if len(self.errors) > 10:
                print("  ... и еще {} ошибок".format(len(self.errors) - 10))

        print("="*60 + "\n")

        # Message box
        if self.failed == 0:
            MessageBox.Show(
                "Конвертация завершена успешно!\n\n"
                "Обработано: {}\n"
                "Время: {:.1f} мин\n"
                "Средняя скорость: {:.1f} сек/файл".format(
                    self.total_files,
                    total_time / 60.0,
                    total_time / self.total_files if self.total_files > 0 else 0
                ),
                "Готово",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
        else:
            MessageBox.Show(
                "Конвертация завершена с ошибками.\n\n"
                "Успешно: {}\n"
                "Ошибок: {}\n"
                "Время: {:.1f} мин\n\n"
                "Подробности в консоли.".format(
                    self.successful, self.failed, total_time / 60.0
                ),
                "Готово",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )


class TransactionFamilyLoadOptions(IFamilyLoadOptions):
    """Custom family load options."""

    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        overwriteParameterValues = True
        return True


def main():
    """Main entry point."""
    try:
        uiapp = __revit__
        converter = FastRFAtoIFCConverter(uiapp)
        converter.run()
    except Exception as e:
        print("Ошибка: {}".format(str(e)))
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
