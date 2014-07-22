# -*- coding: utf-8 -*-

"""
byceps.blueprints.user.forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2014 Jochen Kupperschmidt
"""

from wtforms import Form, PasswordField, TextField
from wtforms.validators import Required, ValidationError


class CreateForm(Form):
    name = TextField('Benutzername', validators=[Required()])
    email_address = TextField('E-Mail-Adresse', validators=[Required()])
    password = PasswordField('Passwort', validators=[Required()])


class LoginForm(Form):
    name = TextField('Benutzername', validators=[Required()])
    password = PasswordField('Passwort', validators=[Required()])
