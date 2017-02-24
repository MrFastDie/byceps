"""
byceps.blueprints.orga_team_admin.authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2017 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from byceps.util.authorization import create_permission_enum


OrgaTeamPermission = create_permission_enum('orga_team', [
    'create',
    'delete',
    'list',
    'administrate_memberships',
])
