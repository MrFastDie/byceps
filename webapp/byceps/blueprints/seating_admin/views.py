# -*- coding: utf-8 -*-

"""
byceps.blueprints.seating_admin.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2016 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from flask import request

from ...util.framework import create_blueprint
from ...util.templating import templated

from ..authorization.decorators import permission_required
from ..authorization.registry import permission_registry
from ..party.models import Party
from ..seating.models import Area, Category

from .authorization import SeatingPermission
from . import service


blueprint = create_blueprint('seating_admin', __name__)


permission_registry.register_enum(SeatingPermission)


@blueprint.route('/<party_id>', defaults={'page': 1})
@blueprint.route('/<party_id>/pages/<int:page>')
@permission_required(SeatingPermission.view)
@templated
def index_for_party(party_id, page):
    """List seating areas for that party."""
    party = Party.query.get_or_404(party_id)

    per_page = request.args.get('per_page', type=int, default=15)

    query = Area.query \
        .for_party(party) \
        .order_by(Area.title)

    areas = query.paginate(page, per_page)

    seat_total_per_area = service.get_seat_total_per_area(party)

    categories = Category.query.for_party(party).all()

    return {
        'party': party,
        'areas': areas,
        'seat_total_per_area': seat_total_per_area,
        'categories': categories,
    }
