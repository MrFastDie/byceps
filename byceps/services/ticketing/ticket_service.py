"""
byceps.services.ticketing.ticket_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2017 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from random import sample
from typing import Dict, Iterator, Optional, Sequence, Set

from flask_sqlalchemy import Pagination

from ...database import db
from ...typing import PartyID, UserID

from ..party.models.party import Party
from ..seating.models.seat import Seat, SeatID
from ..shop.order.models.order import OrderNumber
from ..user.models.user import User

from .models.category import Category, CategoryID
from .models.ticket import Ticket, TicketCode, TicketID
from .models.ticket_bundle import TicketBundle
from . import event_service


# -------------------------------------------------------------------- #
# creation


def create_ticket(category_id: CategoryID, owned_by_id: UserID,
                  *, order_number: Optional[OrderNumber]=None
                 ) -> Sequence[Ticket]:
    """Create a single ticket."""
    tickets = create_tickets(category_id, owned_by_id, 1,
                             order_number=order_number)
    return tickets[0]


def create_tickets(category_id: CategoryID, owned_by_id: UserID, quantity: int,
                   *, order_number: Optional[OrderNumber]=None
                  ) -> Sequence[Ticket]:
    """Create a number of tickets of the same category for a single owner."""
    tickets = list(build_tickets(category_id, owned_by_id, quantity,
                                 order_number=order_number))

    db.session.add_all(tickets)
    db.session.commit()

    return tickets


def build_tickets(category_id: CategoryID, owned_by_id: UserID, quantity: int,
                  *, bundle: Optional[TicketBundle]=None,
                  order_number: Optional[OrderNumber]=None) -> Iterator[Ticket]:
    if quantity < 1:
        raise ValueError('Ticket quantity must be positive.')

    codes = set()  # type: Set[TicketCode]

    for _ in range(quantity):
        code = _generate_ticket_code_not_in(codes)
        codes.add(code)

        yield Ticket(code, category_id, owned_by_id, bundle=bundle,
                     order_number=order_number)


_CODE_ALPHABET = 'BCDFGHJKLMNPQRSTVWXYZ'
_CODE_LENGTH = 5


def _generate_ticket_code() -> TicketCode:
    """Generate a ticket code.

    Generated codes are not necessarily unique!
    """
    return TicketCode(''.join(sample(_CODE_ALPHABET, _CODE_LENGTH)))


def _generate_ticket_code_not_in(codes: Set[TicketCode]) -> TicketCode:
    """Generate ticket codes and return the first one not in the set."""
    while True:
        code = _generate_ticket_code()
        if code not in codes:
            return code


# -------------------------------------------------------------------- #
# revocation


def revoke_ticket(ticket_id: TicketID) -> None:
    """Revoke the ticket."""
    ticket = find_ticket(ticket_id)

    if ticket is None:
        raise ValueError('Unknown ticket ID.')

    ticket.revoked = True

    db.session.commit()


def revoke_tickets(ticket_ids: Set[TicketID]) -> None:
    """Revoke the tickets."""
    tickets = find_tickets(ticket_ids)

    for ticket in tickets:
        ticket.revoked = True

    db.session.commit()


# -------------------------------------------------------------------- #
# lookup


def find_ticket(ticket_id: TicketID) -> Optional[Ticket]:
    """Return the ticket with that id, or `None` if not found."""
    return Ticket.query.get(ticket_id)


def find_ticket_by_code(code: TicketCode) -> Optional[Ticket]:
    """Return the ticket with that code, or `None` if not found."""
    return Ticket.query \
        .filter_by(code=code) \
        .one_or_none()


def find_tickets(ticket_ids: Set[TicketID]) -> Sequence[Ticket]:
    """Return the tickets with those ids."""
    return Ticket.query \
        .filter(Ticket.id.in_(ticket_ids)) \
        .all()


def find_tickets_created_by_order(order_number: OrderNumber
                                 ) -> Sequence[Ticket]:
    """Return the tickets created by this order (as it was marked as paid)."""
    return Ticket.query \
        .filter_by(order_number=order_number) \
        .order_by(Ticket.created_at) \
        .all()


def find_tickets_for_seat_manager(user_id: UserID, party_id: PartyID
                                 ) -> Sequence[Ticket]:
    """Return the tickets for that party whose respective seats the user
    is entitled to manage.
    """
    return Ticket.query \
        .for_party_id(party_id) \
        .filter(Ticket.revoked == False) \
        .filter(
            (
                (Ticket.seat_managed_by_id == None) &
                (Ticket.owned_by_id == user_id)
            ) |
            (Ticket.seat_managed_by_id == user_id)
        ) \
        .options(
            db.joinedload('occupied_seat'),
        ) \
        .all()


def find_tickets_related_to_user(user_id: UserID) -> Sequence[Ticket]:
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


def find_tickets_related_to_user_for_party(user_id: UserID, party_id: PartyID
                                          ) -> Sequence[Ticket]:
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


def find_tickets_used_by_user(user_id: UserID, party_id: PartyID
                             ) -> Sequence[Ticket]:
    """Return the tickets (if any) used by the user for that party."""
    return Ticket.query \
        .for_party_id(party_id) \
        .filter(Ticket.used_by_id == user_id) \
        .outerjoin(Seat) \
        .options(
            db.joinedload('occupied_seat').joinedload('area'),
        ) \
        .order_by(Seat.coord_x, Seat.coord_y) \
        .all()


def uses_any_ticket_for_party(user_id: UserID, party_id: PartyID) -> bool:
    """Return `True` if the user uses any ticket for that party."""
    count = Ticket.query \
        .for_party_id(party_id) \
        .filter(Ticket.used_by_id == user_id) \
        .count()

    return count > 0


def get_ticket_with_details(ticket_id: TicketID) -> Optional[Ticket]:
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


def get_tickets_with_details_for_party_paginated(party_id: PartyID, page: int,
                                                 per_page: int) -> Pagination:
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


def get_tickets_in_use_for_party_paginated(party_id: PartyID, page: int,
                                           per_page: int,
                                           *, search_term: Optional[str]=None
                                          ) -> Pagination:
    """Return the party's tickets which have a user assigned."""
    ticket_user = db.aliased(User)

    query = Ticket.query \
        .for_party_id(party_id) \
        .filter(Ticket.revoked == False) \
        .filter(Ticket.used_by_id.isnot(None))

    if search_term:
        query = query \
            .filter(ticket_user.screen_name.ilike('%{}%'.format(search_term)))

    return query \
        .join(ticket_user, Ticket.used_by_id == ticket_user.id) \
        .order_by(db.func.lower(ticket_user.screen_name), Ticket.created_at) \
        .paginate(page, per_page)


def get_ticket_count_by_party_id() -> Dict[PartyID, int]:
    """Return ticket count (including 0) per party, indexed by party ID."""
    party = db.aliased(Party)

    subquery = db.session \
        .query(
            db.func.count(Ticket.id)
        ) \
        .join(Category) \
        .join(Party) \
        .filter(Party.id == party.id) \
        .filter(Ticket.revoked == False) \
        .subquery() \
        .as_scalar()

    return dict(db.session \
        .query(
            party.id,
            subquery
        ) \
        .all())


def count_tickets_for_party(party_id: PartyID) -> int:
    """Return the number of "sold" (i.e. generated and not revoked)
    tickets for that party.
    """
    return Ticket.query \
        .for_party_id(party_id) \
        .filter(Ticket.revoked == False) \
        .count()


# -------------------------------------------------------------------- #
# user


def appoint_user_manager(ticket_id: TicketID, manager_id: UserID,
                         initiator_id: UserID) -> None:
    """Appoint the user as the ticket's user manager."""
    ticket = find_ticket(ticket_id)

    ticket.user_managed_by_id = manager_id

    event = event_service._build_event('user-manager-appointed', ticket.id, {
        'appointed_user_manager_id': str(manager_id),
        'initiator_id': str(initiator_id),
    })
    db.session.add(event)

    db.session.commit()


def withdraw_user_manager(ticket_id: TicketID, initiator_id: UserID) -> None:
    """Withdraw the ticket's custom user manager."""
    ticket = find_ticket(ticket_id)

    ticket.user_managed_by_id = None

    event = event_service._build_event('user-manager-withdrawn', ticket.id, {
        'initiator_id': str(initiator_id),
    })
    db.session.add(event)

    db.session.commit()


def appoint_user(ticket_id: TicketID, user_id: UserID, initiator_id: UserID
                ) -> None:
    """Appoint the user as the ticket's user."""
    ticket = find_ticket(ticket_id)

    ticket.used_by_id = user_id

    event = event_service._build_event('user-appointed', ticket.id, {
        'appointed_user_id': str(user_id),
        'initiator_id': str(initiator_id),
    })
    db.session.add(event)

    db.session.commit()


def withdraw_user(ticket_id: TicketID, initiator_id: UserID) -> None:
    """Withdraw the ticket's user."""
    ticket = find_ticket(ticket_id)

    ticket.used_by_id = None

    event = event_service._build_event('user-withdrawn', ticket.id, {
        'initiator_id': str(initiator_id),
    })
    db.session.add(event)

    db.session.commit()


# -------------------------------------------------------------------- #
# seat


def appoint_seat_manager(ticket_id: TicketID, manager_id: UserID,
                         initiator_id: UserID) -> None:
    """Appoint the user as the ticket's seat manager."""
    ticket = find_ticket(ticket_id)

    ticket.seat_managed_by_id = manager_id

    event = event_service._build_event('seat-manager-appointed', ticket.id, {
        'appointed_seat_manager_id': str(manager_id),
        'initiator_id': str(initiator_id),
    })
    db.session.add(event)

    db.session.commit()


def withdraw_seat_manager(ticket_id: TicketID, initiator_id: UserID) -> None:
    """Withdraw the ticket's custom seat manager."""
    ticket = find_ticket(ticket_id)

    ticket.seat_managed_by_id = None

    event = event_service._build_event('seat-manager-withdrawn', ticket.id, {
        'initiator_id': str(initiator_id),
    })
    db.session.add(event)

    db.session.commit()


def occupy_seat(ticket_id: TicketID, seat_id: SeatID, initiator_id: UserID
               ) -> None:
    """Occupy the seat with this ticket."""
    ticket = find_ticket(ticket_id)

    _deny_seat_management_if_ticket_belongs_to_bundle(ticket)

    ticket.occupied_seat_id = seat_id

    event = event_service._build_event('seat-occupied', ticket.id, {
        'seat_id': str(seat_id),
        'initiator_id': str(initiator_id),
    })
    db.session.add(event)

    db.session.commit()


def switch_seat(ticket_id: TicketID, new_seat_id: SeatID, initiator_id: UserID
               ) -> None:
    """Release the seat occupied by this ticket and occupy the new seat
    in a single step.
    """
    ticket = find_ticket(ticket_id)

    _deny_seat_management_if_ticket_belongs_to_bundle(ticket)

    old_seat_id = ticket.occupied_seat_id

    ticket.occupied_seat_id = new_seat_id

    event = event_service._build_event('seat-switched', ticket.id, {
        'old_seat_id': str(old_seat_id),
        'new_seat_id': str(new_seat_id),
        'initiator_id': str(initiator_id),
    })
    db.session.add(event)

    db.session.commit()


def release_seat(ticket_id: TicketID, initiator_id: UserID) -> None:
    """Release the seat occupied by this ticket."""
    ticket = find_ticket(ticket_id)

    _deny_seat_management_if_ticket_belongs_to_bundle(ticket)

    ticket.occupied_seat_id = None

    event = event_service._build_event('seat-released', ticket.id, {
        'initiator_id': str(initiator_id),
    })
    db.session.add(event)

    db.session.commit()


class SeatChangeDeniedForBundledTicket(Exception):
    """Indicate that the ticket belongs to a bundle and, thus, must not
    be used to occupy (or release) a single seat.
    """


def _deny_seat_management_if_ticket_belongs_to_bundle(ticket: Ticket) -> None:
    """Raise an exception if this ticket belongs to a bundle.

    A ticket bundle is meant to occupy a matching seat group with the
    appropriate mechanism, not to separately occupy single seats.
    """
    if ticket.belongs_to_bundle:
        raise SeatChangeDeniedForBundledTicket(
            "Ticket '{}' belongs to a bundle and, thus, "
            'must not be used to occupy a single seat.'
            .format(ticket.code))
