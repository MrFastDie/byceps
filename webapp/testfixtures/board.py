# -*- coding: utf-8 -*-

"""
testfixtures.board
~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2016 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from byceps.blueprints.board import service

from .brand import create_brand


def create_category(*, brand=None, number=1, position=None, slug=None,
                    title=None, description=None):
    if brand is None:
        brand = create_brand()

    if position is None:
        position = number

    if slug is None:
        slug = 'category-{}'.format(number)

    if title is None:
        title = 'Kategorie {}'.format(number)

    if description is None:
        description = 'Hier geht es um Kategorie {}'.format(number)

    return service.create_category(brand, position, slug, title, description)


def create_topic(category, creator, *, number=1, title=None, body=None):
    if title is None:
        title = 'Thema {}'.format(number)

    if body is None:
        body = 'Inhalt von Thema {}'.format(number)

    return service.create_topic(category, creator, title, body)


def create_posting(topic, creator, *, number=1, body=None):
    if body is None:
        body = 'Inhalt von Beitrag {}.'.format(number)

    return service.create_posting(topic, creator, body)
