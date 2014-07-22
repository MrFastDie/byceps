# -*- coding: utf-8 -*-

"""
byceps.database
~~~~~~~~~~~~~~~

Database utilities.

:Copyright: 2006-2014 Jochen Kupperschmidt
"""

import uuid

from flask.ext.sqlalchemy import BaseQuery, SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID


db = SQLAlchemy()


db.Uuid = UUID


def generate_uuid():
    """Generate a random UUID (Universally Unique IDentifier)."""
    return uuid.uuid4()
