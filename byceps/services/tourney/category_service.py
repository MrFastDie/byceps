"""
byceps.services.tourney.category_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2018 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from typing import Optional, Sequence

from ...database import db
from ...typing import PartyID

from ..party.models.party import Party as DbParty

from .models.tourney_category import TourneyCategory, TourneyCategoryID


def create_category(party_id: PartyID, title: str) -> TourneyCategory:
    """Create a category for that party."""
    party = DbParty.query.get(party_id)
    if party is None:
        raise ValueError('Unknown party ID "{}"'.format(party_id))

    category = TourneyCategory(party.id, title)
    party.tourney_categories.append(category)

    db.session.commit()

    return category


def update_category(category: TourneyCategory, title: str) -> None:
    """Update category."""
    category.title = title
    db.session.commit()


def move_category_up(category: TourneyCategory) -> None:
    """Move a category upwards by one position."""
    category_list = category.party.tourney_categories

    if category.position == 1:
        raise ValueError('Category already is at the top.')

    popped_category = category_list.pop(category.position - 1)
    category_list.insert(popped_category.position - 2, popped_category)

    db.session.commit()


def move_category_down(category: TourneyCategory) -> None:
    """Move a category downwards by one position."""
    category_list = category.party.tourney_categories

    if category.position == len(category_list):
        raise ValueError('Category already is at the bottom.')

    popped_category = category_list.pop(category.position - 1)
    category_list.insert(popped_category.position, popped_category)

    db.session.commit()


def find_category(category_id: TourneyCategoryID) -> Optional[TourneyCategory]:
    """Return the category with that id, or `None` if not found."""
    return TourneyCategory.query.get(category_id)


def get_categories_for_party(party_id: PartyID) -> Sequence[TourneyCategory]:
    """Return the categories for this party."""
    return TourneyCategory.query \
        .filter_by(party_id=party_id) \
        .order_by(TourneyCategory.position) \
        .all()
