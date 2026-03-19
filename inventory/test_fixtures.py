"""Shared test fixtures used across test modules."""
from decimal import Decimal
from datetime import date, timedelta

from inventory.models import Category, Item, Part, PartOrder, Sale, ModelNote, Auction

TODAY = date.today()
TOMORROW = TODAY + timedelta(days=1)
LAST_WEEK = TODAY - timedelta(days=7)


class InventoryFixtures:
    """Mixin that creates a standard set of interlinked test objects."""

    def make_fixtures(self):
        self.category = Category.objects.create(name='Computer')

        self.item = Item.objects.create(
            name='Dell Desktop',
            make='Dell',
            model='Dimension 8200',
            category=self.category,
            acquisition_date=LAST_WEEK,
            acquisition_source='123 Main St',
            condition=Item.CONDITION_NOT_WORKING,
            status=Item.STATUS_ACQUIRED,
            cost_basis=Decimal('0.00'),
        )

        self.part = Part.objects.create(
            name='512MB RAM',
            description='PC800 RDRAM stick',
            source_item=self.item,
            condition='Good',
            status=Part.STATUS_AVAILABLE,
        )

        self.order = PartOrder.objects.create(
            description='Replacement PSU',
            supplier=PartOrder.SUPPLIER_EBAY,
            order_date=LAST_WEEK,
            total_cost=Decimal('15.00'),
            status=PartOrder.STATUS_ORDERED,
            for_item=self.item,
        )

        self.sale = Sale.objects.create(
            item=self.item,
            sale_date=TODAY,
            sale_price=Decimal('45.00'),
            fees=Decimal('5.00'),
            platform=Sale.PLATFORM_EBAY,
        )

        self.auction = Auction.objects.create(
            item=self.item,
            title='Dell Dimension 8200 Desktop',
            ebay_item_id='123456789',
            starting_bid=Decimal('9.99'),
            start_date=LAST_WEEK,
            end_date=TOMORROW,
            status=Auction.STATUS_ACTIVE,
        )

        self.model_note = ModelNote.objects.create(
            make='Dell',
            model='Dimension 8200',
            category=self.category,
            notes='Uses PC800 RDRAM, max 2GB. Bad caps common.',
        )
