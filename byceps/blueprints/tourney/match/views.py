"""
byceps.blueprints.tourney.match.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2018 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from flask import abort, g, request, url_for

from ....services.tourney import match_service
from ....util.framework.blueprint import create_blueprint
from ....util.framework.templating import templated
from ....util.views import respond_created, respond_no_content

from ...authentication.decorators import api_token_required

from . import signals


blueprint = create_blueprint('tourney_match', __name__)


# -------------------------------------------------------------------- #
# match comments


@blueprint.route('/<uuid:match_id>/comments')
@templated
def comments_view(match_id):
    """Render the comments on a match."""
    match = _get_match_or_404(match_id)

    comments = match_service.get_comments(match.id)

    return {
        'comments': comments,
    }


blueprint.add_url_rule('/<uuid:match_id>/comments/<uuid:comment_id>',
                       endpoint='comment_view',
                       build_only=True)


@blueprint.route('/<uuid:match_id>/comments', methods=['POST'])
@respond_created
def comment_create(match_id):
    """Create a comment on a match."""
    if not g.current_user.is_active:
        abort(403)

    match = _get_match_or_404(match_id)

    body = request.form['body'].strip()

    comment = match_service.create_comment(match_id, g.current_user.id, body)

    signals.match_comment_created.send(None, comment_id=comment.id)

    return url_for('.comment_view', match_id=match.id, comment_id=comment.id)


@blueprint.route('/<uuid:match_id>/comments/<uuid:comment_id>/flags/hidden',
                 methods=['POST'])
@api_token_required
@respond_no_content
def comment_hide(match_id, comment_id):
    """Hide the match comment."""
    initiator_id = request.form.get('initiator_id')
    if not initiator_id:
        abort(400, 'Initiator ID missing')

    match_service.hide_comment(comment_id, initiator_id)


@blueprint.route('/<uuid:match_id>/comments/<uuid:comment_id>/flags/hidden',
                 methods=['DELETE'])
@api_token_required
@respond_no_content
def comment_unhide(match_id, comment_id):
    """Un-hide the match comment."""
    initiator_id = request.form.get('initiator_id')
    if not initiator_id:
        abort(400, 'Initiator ID missing')

    match_service.unhide_comment(comment_id, initiator_id)


def _get_match_or_404(match_id):
    match = match_service.find_match(match_id)

    if match is None:
        abort(404)

    return match
