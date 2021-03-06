"""
:Copyright: 2006-2018 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from unittest.mock import patch

from byceps.services.shop.cart.models import Cart
from byceps.services.shop.order.transfer.models import PaymentMethod
from byceps.services.shop.order import service as order_service
from byceps.services.shop.sequence import service as shop_sequence_service
from byceps.services.shop.sequence.transfer.models import Purpose

from testfixtures.shop_order import create_orderer

from tests.services.shop.base import ShopTestBase


ANY_PAYMENT_METHOD = PaymentMethod.bank_transfer


class OrderActionTestBase(ShopTestBase):

    def setUp(self):
        super().setUp()

        self.create_brand_and_party()

        self.shop = self.create_shop(self.party.id)

        self.admin = self.create_user_with_detail('Admin')
        self.buyer = self.create_user_with_detail('Buyer')

        shop_sequence_service.create_sequence(self.shop.id, Purpose.order,
                                              prefix='article-')

    # -------------------------------------------------------------------- #
    # helpers

    @patch('byceps.blueprints.shop_order.signals.order_placed.send')
    def create_order(self, articles_with_quantity, order_placed_mock):
        orderer = create_orderer(self.buyer)

        cart = Cart()
        for article, quantity in articles_with_quantity:
            cart.add_item(article, quantity)

        return order_service.create_order(self.shop.id, orderer,
            ANY_PAYMENT_METHOD, cart)

    def mark_order_as_paid(self):
        order_service.mark_order_as_paid(self.order.id, ANY_PAYMENT_METHOD,
            self.admin.id)
