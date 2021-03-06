"""
byceps.services.board.topic_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2018 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from datetime import datetime
from typing import Optional, Set

from flask_sqlalchemy import Pagination

from ...database import db
from ...typing import UserID

from ..user.models.user import User

from .aggregation_service import aggregate_category, aggregate_topic
from .models.category import Category as DbCategory
from .models.posting import InitialTopicPostingAssociation, Posting as DbPosting
from .models.topic import Topic as DbTopic
from .posting_service import update_posting
from .transfer.models import BoardID, CategoryID, TopicID


def count_topics_for_board(board_id: BoardID) -> int:
    """Return the number of topics for that board."""
    return DbTopic.query \
        .join(DbCategory).filter(DbCategory.board_id == board_id) \
        .count()


def find_topic_by_id(topic_id: TopicID) -> Optional[DbTopic]:
    """Return the topic with that id, or `None` if not found."""
    return DbTopic.query.get(topic_id)


def find_topic_visible_for_user(topic_id: TopicID, user: User
                               ) -> Optional[DbTopic]:
    """Return the topic with that id, or `None` if not found or
    invisible for the user.
    """
    return DbTopic.query \
        .options(
            db.joinedload(DbTopic.category),
        ) \
        .only_visible_for_user(user) \
        .filter_by(id=topic_id) \
        .first()


def get_all_topic_ids_in_category(category_id: CategoryID) -> Set[TopicID]:
    """Return the IDs of all topics in the category."""
    rows = db.session \
        .query(DbTopic.id) \
        .filter(DbTopic.category_id == category_id) \
        .all()

    return {row[0] for row in rows}


def paginate_topics(category_id: CategoryID, user: User, page: int,
                    topics_per_page: int) -> Pagination:
    """Paginate topics in that category, as visible for the user.

    Pinned topics are returned first.
    """
    return DbTopic.query \
        .for_category(category_id) \
        .options(
            db.joinedload(DbTopic.category),
            db.joinedload(DbTopic.creator),
            db.joinedload(DbTopic.last_updated_by),
            db.joinedload(DbTopic.hidden_by),
            db.joinedload(DbTopic.locked_by),
            db.joinedload(DbTopic.pinned_by),
        ) \
        .only_visible_for_user(user) \
        .order_by(DbTopic.pinned.desc(), DbTopic.last_updated_at.desc()) \
        .paginate(page, topics_per_page)


def create_topic(category_id: CategoryID, creator_id: UserID, title: str,
                 body: str) -> DbTopic:
    """Create a topic with an initial posting in that category."""
    topic = DbTopic(category_id, creator_id, title)
    posting = DbPosting(topic, creator_id, body)
    initial_topic_posting_association = InitialTopicPostingAssociation(topic,
                                                                       posting)

    db.session.add(topic)
    db.session.add(posting)
    db.session.add(initial_topic_posting_association)
    db.session.commit()

    aggregate_topic(topic)

    return topic


def update_topic(topic: DbTopic, editor_id: UserID, title: str, body: str
                ) -> None:
    """Update the topic (and its initial posting)."""
    topic.title = title.strip()

    update_posting(topic.initial_posting, editor_id, body, commit=False)

    db.session.commit()


def find_default_posting_to_jump_to(topic_id: TopicID, user: User,
                                    last_viewed_at: Optional[datetime]
                                   ) -> Optional[DbPosting]:
    """Return the posting of the topic to show by default, or `None`."""
    if user.is_anonymous:
        # All postings are potentially new to a guest, so start on
        # the first page.
        return None

    if last_viewed_at is None:
        # This topic is completely new to the current user, so
        # start on the first page.
        return None

    postings_query = DbPosting.query \
        .for_topic(topic_id) \
        .only_visible_for_user(user)

    first_new_posting = postings_query \
        .filter(DbPosting.created_at > last_viewed_at) \
        .earliest_to_latest() \
        .first()

    if first_new_posting is None:
        # Current user has seen all postings so far, so show the last one.
        return postings_query \
            .latest_to_earliest() \
            .first()

    return first_new_posting


def hide_topic(topic: DbTopic, hidden_by_id: UserID) -> None:
    """Hide the topic."""
    topic.hidden = True
    topic.hidden_at = datetime.now()
    topic.hidden_by_id = hidden_by_id
    db.session.commit()

    aggregate_topic(topic)


def unhide_topic(topic: DbTopic, unhidden_by_id: UserID) -> None:
    """Un-hide the topic."""
    # TODO: Store who un-hid the topic.
    topic.hidden = False
    topic.hidden_at = None
    topic.hidden_by_id = None
    db.session.commit()

    aggregate_topic(topic)


def lock_topic(topic: DbTopic, locked_by_id: UserID) -> None:
    """Lock the topic."""
    topic.locked = True
    topic.locked_at = datetime.now()
    topic.locked_by_id = locked_by_id
    db.session.commit()


def unlock_topic(topic: DbTopic, unlocked_by_id: UserID) -> None:
    """Unlock the topic."""
    # TODO: Store who unlocked the topic.
    topic.locked = False
    topic.locked_at = None
    topic.locked_by_id = None
    db.session.commit()


def pin_topic(topic: DbTopic, pinned_by_id: UserID) -> None:
    """Pin the topic."""
    topic.pinned = True
    topic.pinned_at = datetime.now()
    topic.pinned_by_id = pinned_by_id
    db.session.commit()


def unpin_topic(topic: DbTopic, unpinned_by_id: UserID) -> None:
    """Unpin the topic."""
    # TODO: Store who unpinned the topic.
    topic.pinned = False
    topic.pinned_at = None
    topic.pinned_by_id = None
    db.session.commit()


def move_topic(topic: DbTopic, new_category_id: CategoryID) -> None:
    """Move the topic to another category."""
    old_category = topic.category
    new_category = DbCategory.query.get(new_category_id)

    topic.category = new_category
    db.session.commit()

    for category in old_category, new_category:
        aggregate_category(category)
