# -*- coding: utf-8 -*-

"""
byceps.services.authentication.password.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2016 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from ....database import db


class Credential(db.Model):
    """A user's login credential."""
    __tablename__ = 'authn_credentials'

    user_id = db.Column(db.Uuid, db.ForeignKey('users.id'), primary_key=True)
    password_hash = db.Column(db.Unicode(80), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, user_id, password_hash, updated_at):
        self.user_id = user_id
        self.password_hash = password_hash
        self.updated_at = updated_at