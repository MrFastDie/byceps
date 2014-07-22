# -*- coding: utf-8 -*-

"""
byceps.util.framework
~~~~~~~~~~~~~~~~~~~~~

Framework utilities.

:Copyright: 2006-2014 Jochen Kupperschmidt
"""

from importlib import import_module

from flask import Blueprint, flash


# -------------------------------------------------------------------- #
# configuration


def load_config(app, module_name):
    """Load the configuration from the specified module.

    The module is expected to be located in the 'config' sub-package.
    """
    module_path = 'config.{}'.format(module_name)
    app.config.from_object(module_path)


# -------------------------------------------------------------------- #
# blueprints


def create_blueprint(name, import_name):
    """Create a blueprint with default folder names."""
    return Blueprint(
        name, import_name,
        static_folder='static',
        template_folder='templates')


def register_blueprint(app, name, url_prefix):
    """Register a blueprint with the application.

    The module with the given name is expected to be located inside the
    'blueprints' sub-package and to contain a blueprint instance named
    'blueprint'.
    """
    module = import_module('byceps.blueprints.{}.views'.format(name))
    blueprint = getattr(module, 'blueprint')
    app.register_blueprint(blueprint, url_prefix=url_prefix)


# -------------------------------------------------------------------- #
# message flashing


def flash_error(message, *args):
    """Flash a message indicating an error."""
    return _flash(message, *args, category='error')


def flash_success(message, *args):
    """Flash a message describing a successful action."""
    return _flash(message, *args, category='success')


def _flash(message, *args, category=None):
    return flash(message.format(*args), category=category)
