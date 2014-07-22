#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
management script
~~~~~~~~~~~~~~~~~

Run the application, take administrative action.

:Copyright: 2006-2014 Jochen Kupperschmidt
"""

from flask.ext.script import Manager

from byceps.application import create_app
from byceps.database import db


CONFIG_NAME = 'development'


app = create_app(CONFIG_NAME)

manager = Manager(app)


@manager.shell
def make_shell_context():
    return {
        'app': app,
        'db': db,
    }


if __name__ == '__main__':
    manager.run()
