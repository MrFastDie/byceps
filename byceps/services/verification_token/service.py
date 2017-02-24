"""
byceps.services.verification_token.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2017 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from ...database import db

from .models import Purpose, Token


def find_or_create_for_email_address_confirmation(user_id):
    token = find_for_email_address_confirmation_by_user(user_id)
    if token is None:
        token = build_for_email_address_confirmation(user_id)
        db.session.add(token)
        db.session.commit()
    return token


def find_or_create_for_terms_consent(user_id):
    token = find_for_terms_consent_by_user(user_id)
    if token is None:
        token = build_for_terms_consent(user_id)
        db.session.add(token)
        db.session.commit()
    return token


def build_for_email_address_confirmation(user_id):
    return Token(user_id, Purpose.email_address_confirmation)


def build_for_password_reset(user_id):
    return Token(user_id, Purpose.password_reset)


def build_for_terms_consent(user_id):
    return Token(user_id, Purpose.terms_consent)


def find_for_email_address_confirmation_by_token(token):
    purpose = Purpose.email_address_confirmation
    return find_for_purpose_by_token(token, purpose)


def find_for_email_address_confirmation_by_user(user_id):
    return Token.query \
        .filter_by(user_id=user_id) \
        .for_purpose(Purpose.email_address_confirmation) \
        .first()


def find_for_password_reset_by_token(token):
    purpose = Purpose.password_reset
    return find_for_purpose_by_token(token, purpose)


def find_for_terms_consent_by_token(token):
    purpose = Purpose.terms_consent
    return find_for_purpose_by_token(token, purpose)


def find_for_terms_consent_by_user(user_id):
    return Token.query \
        .filter_by(user_id=user_id) \
        .for_purpose(Purpose.terms_consent) \
        .first()


def find_for_purpose_by_token(token, purpose):
    return Token.query \
        .filter_by(token=token) \
        .for_purpose(purpose) \
        .first()
