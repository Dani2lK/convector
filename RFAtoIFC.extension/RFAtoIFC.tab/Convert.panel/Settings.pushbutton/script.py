# -*- coding: utf-8 -*-
"""Settings for RFA to IFC converter - configure template projects."""

import sys
import os

# Add lib folder to path
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
lib_path = os.path.join(script_dir, 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

from config_manager import ConfigManager
from ui_helpers import TemplateConfigDialog

from System.Windows.Forms import Application, DialogResult


def main():
    """Main entry point for settings configuration."""
    try:
        # Initialize configuration manager
        config_manager = ConfigManager()

        # Show configuration dialog
        dialog = TemplateConfigDialog(config_manager)
        Application.Run(dialog)

        # Check if configuration was saved
        if dialog.result == DialogResult.OK:
            print("Настройки шаблонов успешно сохранены!")
        else:
            print("Настройка отменена.")

    except Exception as e:
        print("Ошибка при настройке: {}".format(str(e)))
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
