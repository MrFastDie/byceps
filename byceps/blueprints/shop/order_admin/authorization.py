"""
byceps.blueprints.shop.order_admin.authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2018 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from byceps.util.authorization import create_permission_enum


ShopOrderPermission = create_permission_enum('shop_order', [
    'cancel',
    'mark_as_paid',
    'update',
    'view',
])
