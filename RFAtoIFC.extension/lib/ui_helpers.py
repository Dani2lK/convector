# -*- coding: utf-8 -*-
"""UI helpers for file selection and user interaction."""

import os
import clr
import sys
import threading
import time

clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from System.Windows.Forms import (
    Form, Button, Label, TextBox, FolderBrowserDialog, OpenFileDialog,
    DialogResult, FormBorderStyle, FormStartPosition, MessageBox,
    MessageBoxButtons, MessageBoxIcon, Application
)
from System.Drawing import Point, Size, Font, FontStyle


class TemplateConfigDialog(Form):
    """Dialog for configuring template project paths."""

    def __init__(self, config_manager):
        """Initialize template configuration dialog.

        Args:
            config_manager: ConfigManager instance
        """
        self.config_manager = config_manager
        self.result = DialogResult.Cancel

        # Form settings
        self.Text = 'Настройка шаблонов проектов'
        self.Width = 650
        self.Height = 500  # Увеличено с 400 до 500
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = False
        self.MinimizeBox = False

        # Template types with Russian labels
        self.templates = [
            ('wall', 'Проект со стеной'),
            ('floor', 'Проект с полом'),
            ('ceiling', 'Проект с потолком'),
            ('roof', 'Проект с крышей'),
            ('standalone', 'Пустой проект (standalone)')
        ]

        self.textboxes = {}
        self._create_controls()

    def _create_controls(self):
        """Create form controls."""
        y_pos = 20

        # Title label
        title = Label()
        title.Text = 'Укажите пути к шаблонам проектов Revit (.rvt):'
        title.Location = Point(20, y_pos)
        title.Size = Size(600, 20)
        title.Font = Font(title.Font, FontStyle.Bold)
        self.Controls.Add(title)

        y_pos += 40

        # Create controls for each template type
        for template_type, label_text in self.templates:
            # Label
            label = Label()
            label.Text = label_text + ':'
            label.Location = Point(20, y_pos)
            label.Size = Size(200, 20)
            self.Controls.Add(label)

            # TextBox
            textbox = TextBox()
            textbox.Location = Point(20, y_pos + 25)
            textbox.Size = Size(500, 20)
            textbox.Text = self.config_manager.get_template_path(template_type)
            self.Controls.Add(textbox)
            self.textboxes[template_type] = textbox

            # Browse button
            browse_btn = Button()
            browse_btn.Text = '...'
            browse_btn.Location = Point(530, y_pos + 23)
            browse_btn.Size = Size(80, 24)
            browse_btn.Tag = template_type
            browse_btn.Click += self._browse_click
            self.Controls.Add(browse_btn)

            y_pos += 60

        # Save button
        save_btn = Button()
        save_btn.Text = 'Сохранить'
        save_btn.Location = Point(430, y_pos + 10)
        save_btn.Size = Size(100, 30)
        save_btn.Click += self._save_click
        self.Controls.Add(save_btn)

        # Cancel button
        cancel_btn = Button()
        cancel_btn.Text = 'Отмена'
        cancel_btn.Location = Point(320, y_pos + 10)
        cancel_btn.Size = Size(100, 30)
        cancel_btn.Click += self._cancel_click
        self.Controls.Add(cancel_btn)

    def _browse_click(self, sender, e):
        """Handle browse button click."""
        template_type = sender.Tag

        dialog = OpenFileDialog()
        dialog.Filter = 'Revit Project Files (*.rvt)|*.rvt'
        dialog.Title = 'Выберите файл шаблона проекта'

        if dialog.ShowDialog() == DialogResult.OK:
            self.textboxes[template_type].Text = dialog.FileName

    def _save_click(self, sender, e):
        """Handle save button click."""
        # Validate all paths
        for template_type, textbox in self.textboxes.items():
            path = textbox.Text.strip()
            if not path:
                MessageBox.Show(
                    'Пожалуйста, укажите путь для всех шаблонов.',
                    'Ошибка',
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                )
                return

            if not os.path.exists(path):
                MessageBox.Show(
                    'Файл не найден:\n{}'.format(path),
                    'Ошибка',
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                )
                return

            # Save to config
            self.config_manager.set_template_path(template_type, path)

        self.result = DialogResult.OK
        self.Close()

    def _cancel_click(self, sender, e):
        """Handle cancel button click."""
        self.result = DialogResult.Cancel
        self.Close()


class FileSelectionHelper:
    """Helper class for file and folder selection dialogs."""

    @staticmethod
    def select_rfa_file_or_folder(default_folder=''):
        """Show dialog to select RFA file or folder.

        Args:
            default_folder: Default folder to open in dialog

        Returns:
            Tuple: (path: str, is_folder: bool) or (None, None) if cancelled
        """
        # Show options dialog
        form = Form()
        form.Text = 'Выбор файлов RFA'
        form.Width = 400
        form.Height = 200
        form.FormBorderStyle = FormBorderStyle.FixedDialog
        form.StartPosition = FormStartPosition.CenterScreen
        form.MaximizeBox = False
        form.MinimizeBox = False

        label = Label()
        label.Text = 'Что вы хотите конвертировать?'
        label.Location = Point(20, 20)
        label.Size = Size(350, 20)
        form.Controls.Add(label)

        file_btn = Button()
        file_btn.Text = 'Выбрать файл .rfa'
        file_btn.Location = Point(80, 60)
        file_btn.Size = Size(230, 35)
        form.Controls.Add(file_btn)

        folder_btn = Button()
        folder_btn.Text = 'Выбрать папку с .rfa файлами'
        folder_btn.Location = Point(80, 105)
        folder_btn.Size = Size(230, 35)
        form.Controls.Add(folder_btn)

        result = {'path': None, 'is_folder': None}

        def file_click(s, e):
            dialog = OpenFileDialog()
            dialog.Filter = 'Revit Family Files (*.rfa)|*.rfa'
            dialog.Title = 'Выберите файл RFA'
            if default_folder and os.path.exists(default_folder):
                dialog.InitialDirectory = default_folder

            if dialog.ShowDialog() == DialogResult.OK:
                result['path'] = dialog.FileName
                result['is_folder'] = False
                form.Close()

        def folder_click(s, e):
            dialog = FolderBrowserDialog()
            dialog.Description = 'Выберите папку с файлами RFA'
            if default_folder and os.path.exists(default_folder):
                dialog.SelectedPath = default_folder

            if dialog.ShowDialog() == DialogResult.OK:
                result['path'] = dialog.SelectedPath
                result['is_folder'] = True
                form.Close()

        file_btn.Click += file_click
        folder_btn.Click += folder_click

        Application.Run(form)

        return result['path'], result['is_folder']

    @staticmethod
    def select_export_folder(default_folder=''):
        """Show dialog to select export folder.

        Args:
            default_folder: Default folder to open in dialog

        Returns:
            String: Selected folder path or None if cancelled
        """
        dialog = FolderBrowserDialog()
        dialog.Description = 'Выберите папку для экспорта IFC файлов'

        if default_folder and os.path.exists(default_folder):
            dialog.SelectedPath = default_folder

        if dialog.ShowDialog() == DialogResult.OK:
            return dialog.SelectedPath

        return None


class RevitActivitySimulator:
    """Simulates Revit activity to prevent taskbar flashing."""

    def __init__(self, uiapp):
        """Initialize activity simulator.

        Args:
            uiapp: Revit UIApplication
        """
        self.uiapp = uiapp
        self.running = False
        self.thread = None

    def start(self):
        """Start activity simulation."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._simulate_activity)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        """Stop activity simulation."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def _simulate_activity(self):
        """Simulate activity in background thread."""
        try:
            while self.running:
                # Simulate activity by checking application status
                # This helps prevent Revit from flashing in taskbar
                if self.uiapp and self.uiapp.Application:
                    # Simple check to maintain activity
                    _ = self.uiapp.Application.VersionName

                # Wait before next check
                time.sleep(1)

        except Exception as e:
            print("Activity simulation error: {}".format(str(e)))


class DialogHandler:
    """Handles automatic dismissal of Revit warning dialogs."""

    def __init__(self, uiapp):
        """Initialize dialog handler.

        Args:
            uiapp: Revit UIApplication
        """
        self.uiapp = uiapp
        self.failure_handler = AutoDismissFailureHandler()

    def register(self):
        """Register failure handler."""
        try:
            from Autodesk.Revit.DB import FailureHandlingOptions
            # Handler will be registered per transaction
            return True
        except Exception as e:
            print("Error registering dialog handler: {}".format(str(e)))
            return False


class AutoDismissFailureHandler:
    """Custom failure handler to automatically dismiss warnings."""

    def ProcessFailures(self, failures_accessor):
        """Process failures and dismiss warnings.

        Args:
            failures_accessor: FailuresAccessor instance

        Returns:
            FailureProcessingResult
        """
        from Autodesk.Revit.DB import (
            FailureProcessingResult, FailureSeverity
        )

        try:
            # Get all failure messages
            failure_messages = failures_accessor.GetFailureMessages()

            for failure in failure_messages:
                # Get severity
                severity = failure.GetSeverity()

                # Dismiss warnings and errors if possible
                if severity == FailureSeverity.Warning:
                    failures_accessor.DeleteWarning(failure)
                elif severity == FailureSeverity.Error:
                    # Try to resolve errors
                    if failure.HasResolutions():
                        failures_accessor.ResolveFailure(failure)
                    else:
                        # Delete if can't resolve
                        try:
                            failures_accessor.DeleteWarning(failure)
                        except:
                            pass

            return FailureProcessingResult.Continue

        except Exception as e:
            print("Error in failure handler: {}".format(str(e)))
            return FailureProcessingResult.Continue
