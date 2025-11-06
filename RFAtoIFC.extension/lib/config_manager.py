# -*- coding: utf-8 -*-
"""Configuration manager for RFA to IFC converter."""

import os
import json
import codecs

class ConfigManager:
    """Manages configuration for template project paths."""

    def __init__(self, config_path=None):
        """Initialize configuration manager.

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            # Get the extension directory
            ext_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(os.path.dirname(ext_dir), 'config')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            config_path = os.path.join(config_dir, 'templates_config.json')

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with codecs.open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print("Error loading config: {}".format(str(e)))
                return self._get_default_config()
        return self._get_default_config()

    def _get_default_config(self):
        """Get default configuration structure."""
        return {
            'templates': {
                'wall': '',
                'floor': '',
                'ceiling': '',
                'roof': '',
                'standalone': ''
            },
            'last_export_folder': '',
            'last_rfa_folder': ''
        }

    def save_config(self):
        """Save configuration to file."""
        try:
            with codecs.open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print("Error saving config: {}".format(str(e)))
            return False

    def get_template_path(self, template_type):
        """Get template path for specified type.

        Args:
            template_type: One of 'wall', 'floor', 'ceiling', 'roof', 'standalone'

        Returns:
            Path to template file or empty string if not set.
        """
        return self.config.get('templates', {}).get(template_type, '')

    def set_template_path(self, template_type, path):
        """Set template path for specified type.

        Args:
            template_type: One of 'wall', 'floor', 'ceiling', 'roof', 'standalone'
            path: Path to template file
        """
        if 'templates' not in self.config:
            self.config['templates'] = {}
        self.config['templates'][template_type] = path
        self.save_config()

    def is_configured(self):
        """Check if all required templates are configured.

        Returns:
            True if all templates are set, False otherwise.
        """
        templates = self.config.get('templates', {})
        required = ['wall', 'floor', 'ceiling', 'roof', 'standalone']

        for template_type in required:
            path = templates.get(template_type, '')
            if not path or not os.path.exists(path):
                return False

        return True

    def get_last_export_folder(self):
        """Get last used export folder."""
        return self.config.get('last_export_folder', '')

    def set_last_export_folder(self, path):
        """Set last used export folder."""
        self.config['last_export_folder'] = path
        self.save_config()

    def get_last_rfa_folder(self):
        """Get last used RFA folder."""
        return self.config.get('last_rfa_folder', '')

    def set_last_rfa_folder(self, path):
        """Set last used RFA folder."""
        self.config['last_rfa_folder'] = path
        self.save_config()
