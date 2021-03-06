"""
byceps.services.user.event_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2018 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from datetime import datetime
from typing import Optional, Sequence

from ...database import db
from ...typing import UserID

from .models.event import UserEvent, UserEventData


def create_event(event_type: str, user_id: UserID, data: UserEventData) -> None:
    """Create a user event."""
    event = _build_event(event_type, user_id, data)

    db.session.add(event)
    db.session.commit()


def _build_event(event_type: str, user_id: UserID, data: UserEventData,
                 occurred_at: Optional[datetime]=None) -> UserEvent:
    """Assemble, but not persist, a user event."""
    if occurred_at is None:
        occurred_at = datetime.utcnow()

    return UserEvent(occurred_at, event_type, user_id, data)


def get_events_for_user(user_id: UserID) -> Sequence[UserEvent]:
    """Return the events for that user."""
    return UserEvent.query \
        .filter_by(user_id=user_id) \
        .order_by(UserEvent.occurred_at) \
        .all()
