"""
byceps.services.ticketing.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2017 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from collections import defaultdict
from datetime import datetime
from itertools import chain

from ...database import db

from ..party.models import Party
from ..party import service as party_service
from ..seating.models.category import Category
from ..seating.models.seat import Seat
from ..user import service as user_service

from .models.archived_attendance import ArchivedAttendance
from .models.ticket import Ticket
from .models.ticket_bundle import TicketBundle


# -------------------------------------------------------------------- #
# tickets


def create_ticket(category, owned_by_id):
    """Create a single ticket."""
    return create_tickets(category, owned_by_id, 1)


def create_tickets(category, owned_by_id, quantity):
    """Create a number of tickets of the same category for a single owner."""
    tickets = list(_build_tickets(category, owned_by_id, quantity))

    db.session.add_all(tickets)
    db.session.commit()

    return tickets


def _build_tickets(category, owned_by_id, quantity, *, bundle=None):
    if quantity < 1:
        raise ValueError('Ticket quantity must be positive.')

    for _ in range(quantity):
        yield Ticket(category, owned_by_id, bundle=bundle)


def find_ticket(ticket_id):
    """Return the ticket with that id, or `None` if not found."""
    return Ticket.query.get(ticket_id)


def find_tickets_related_to_user(user_id):
    """Return tickets related to the user."""
    return Ticket.query \
        .filter(
            (Ticket.owned_by_id == user_id) |
            (Ticket.seat_managed_by_id == user_id) |
            (Ticket.user_managed_by_id == user_id) |
            (Ticket.used_by_id == user_id)
        ) \
        .options(
            db.joinedload('occupied_seat').joinedload('area'),
            db.joinedload('occupied_seat').joinedload('category'),
            db.joinedload('seat_managed_by'),
            db.joinedload('user_managed_by'),
            db.joinedload('used_by'),
        ) \
        .order_by(Ticket.created_at) \
        .all()


def find_tickets_related_to_user_for_party(user_id, party_id):
    """Return tickets related to the user for the party."""
    return Ticket.query \
        .for_party_id(party_id) \
        .filter(
            (Ticket.owned_by_id == user_id) |
            (Ticket.seat_managed_by_id == user_id) |
            (Ticket.user_managed_by_id == user_id) |
            (Ticket.used_by_id == user_id)
        ) \
        .options(
            db.joinedload('occupied_seat').joinedload('area'),
            db.joinedload('occupied_seat').joinedload('category'),
            db.joinedload('seat_managed_by'),
            db.joinedload('user_managed_by'),
            db.joinedload('used_by'),
        ) \
        .order_by(Ticket.created_at) \
        .all()


def find_tickets_used_by_user(user_id, party_id):
    """Return the tickets (if any) used by the user for that party."""
    return Ticket.query \
        .for_party_id(party_id) \
        .filter(Ticket.used_by_id == user_id) \
        .join(Seat) \
        .options(
            db.joinedload('occupied_seat').joinedload('area'),
        ) \
        .order_by(Seat.coord_x, Seat.coord_y) \
        .all()


def uses_any_ticket_for_party(user_id, party_id):
    """Return `True` if the user uses any ticket for that party."""
    count = Ticket.query \
        .for_party_id(party_id) \
        .filter(Ticket.used_by_id == user_id) \
        .count()

    return count > 0


def get_attended_parties(user_id):
    """Return the parties the user has attended in the past."""
    ticket_attendance_party_ids = _get_attended_party_ids(user_id)
    archived_attendance_party_ids = _get_archived_attendance_party_ids(user_id)

    party_ids = frozenset(chain(ticket_attendance_party_ids, archived_attendance_party_ids))

    parties = party_service.get_parties(party_ids)

    return [party.to_tuple() for party in parties]


def _get_attended_party_ids(user_id):
    """Return the IDs of the non-legacy parties the user has attended."""
    # Note: Party dates aren't UTC, yet.
    party_id_rows = db.session \
        .query(Party.id) \
        .filter(Party.ends_at < datetime.now()) \
        .join(Category).join(Ticket).filter(Ticket.used_by_id == user_id) \
        .all()

    return _get_first_column_values_as_set(party_id_rows)


def get_ticket_with_details(ticket_id):
    """Return the ticket with that id, or `None` if not found."""
    return Ticket.query \
        .options(
            db.joinedload('category'),
            db.joinedload('occupied_seat').joinedload('area'),
            db.joinedload('owned_by'),
            db.joinedload('seat_managed_by'),
            db.joinedload('user_managed_by'),
        ) \
        .get(ticket_id)


def get_tickets_with_details_for_party_paginated(party_id, page, per_page):
    """Return the party's tickets to show on the specified page."""
    return Ticket.query \
        .for_party_id(party_id) \
        .options(
            db.joinedload('category'),
            db.joinedload('owned_by'),
            db.joinedload('occupied_seat').joinedload('area'),
        ) \
        .order_by(Ticket.created_at) \
        .paginate(page, per_page)


def get_ticket_count_by_party_id():
    """Return ticket count (including 0) per party, indexed by party ID."""
    return dict(db.session \
        .query(
            Party.id,
            db.func.count(Ticket.id)
        ) \
        .outerjoin(Category) \
        .outerjoin(Ticket) \
        .group_by(Party.id) \
        .all())


def count_tickets_for_party(party_id):
    """Return the number of "sold" (i.e. generated) tickets for that party."""
    return Ticket.query \
        .for_party_id(party_id) \
        .count()


def get_attendees_by_party(parties):
    """Return the parties' attendees, indexed by party."""
    if not parties:
        return {}

    party_ids = frozenset(party.id for party in parties)

    attendee_ids_by_party_id = get_attendee_ids_for_parties(party_ids)

    all_attendee_ids = frozenset(
        chain.from_iterable(attendee_ids_by_party_id.values()))
    all_attendees = user_service.find_users(all_attendee_ids)
    all_attendees_by_id = {user.id: user for user in all_attendees}

    attendees_by_party = {}
    for party in parties:
        attendee_ids = attendee_ids_by_party_id.get(party.id, frozenset())

        attendees = frozenset(all_attendees_by_id[attendee_id]
                              for attendee_id in attendee_ids)

        attendees_by_party[party] = attendees

    return attendees_by_party


def get_attendee_ids_for_parties(party_ids):
    """Return the partys' attendee IDs, indexed by party ID."""
    if not party_ids:
        return {}

    rows = db.session \
        .query(Category.party_id, Ticket.used_by_id) \
        .filter(Category.party_id.in_(party_ids)) \
        .join(Ticket) \
        .filter(Ticket.used_by_id != None) \
        .all()

    attendee_ids_by_party_id = defaultdict(set)
    for party_id, attendee_id in rows:
        attendee_ids_by_party_id[party_id].add(attendee_id)

    return dict(attendee_ids_by_party_id)


# -------------------------------------------------------------------- #
# ticket bundles


def create_ticket_bundle(category, ticket_quantity, owned_by_id):
    """Create a ticket bundle and the given quantity of tickets."""
    if ticket_quantity < 1:
        raise ValueError('Ticket quantity must be positive.')

    bundle = TicketBundle(category.id, ticket_quantity, owned_by_id)
    db.session.add(bundle)

    tickets = list(_build_tickets(category, owned_by_id, ticket_quantity,
                                  bundle=bundle))
    db.session.add_all(tickets)

    db.session.commit()

    return bundle


def delete_ticket_bundle(bundle):
    """Delete the ticket bundle and the tickets associated with it."""
    for ticket in bundle.tickets:
        db.session.delete(ticket)

    db.session.delete(bundle)

    db.session.commit()


# -------------------------------------------------------------------- #
# archived attendances


def create_archived_attendance(user_id, party_id):
    """Create an archived attendance of the user at the party."""
    attendance = ArchivedAttendance(user_id, party_id)

    db.session.add(attendance)
    db.session.commit()

    return attendance


def _get_archived_attendance_party_ids(user_id):
    """Return the IDs of the legacy parties the user has attended."""
    party_id_rows = db.session \
        .query(ArchivedAttendance.party_id) \
        .filter(ArchivedAttendance.user_id == user_id) \
        .all()

    return _get_first_column_values_as_set(party_id_rows)


# -------------------------------------------------------------------- #
# helpers


def _get_first_column_values_as_set(rows):
    """Return the first element of each row as a set."""
    return frozenset(row[0] for row in rows)
