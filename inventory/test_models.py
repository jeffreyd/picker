from decimal import Decimal
from datetime import date, timedelta

from django.db import IntegrityError
from django.test import TestCase

from inventory.models import Category, Item, Part, PartOrder, Sale, ModelNote, Auction

TODAY = date.today()
LAST_WEEK = TODAY - timedelta(days=7)
TOMORROW = TODAY + timedelta(days=1)


class CategoryModelTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Computer')

    def test_str(self):
        self.assertEqual(str(self.cat), 'Computer')

    def test_ordering_alphabetical(self):
        Category.objects.create(name='TV')
        Category.objects.create(name='Monitor')
        names = list(Category.objects.values_list('name', flat=True))
        self.assertEqual(names, sorted(names))


class ItemModelTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Computer')
        self.item = Item.objects.create(
            name='Dell Desktop', make='Dell', model='Dimension 8200',
            category=self.cat, acquisition_date=LAST_WEEK, cost_basis=Decimal('0.00'),
        )

    def test_str_with_make_and_model(self):
        self.assertEqual(str(self.item), 'Dell Dimension 8200')

    def test_str_fallback_to_name(self):
        item = Item.objects.create(name='Mystery Box', acquisition_date=TODAY)
        self.assertEqual(str(item), 'Mystery Box')

    def test_display_name_with_make_and_model(self):
        self.assertEqual(self.item.display_name, 'Dell Dimension 8200')

    def test_display_name_fallback(self):
        self.assertEqual(Item(name='Mystery Box').display_name, 'Mystery Box')

    def test_get_absolute_url(self):
        self.assertEqual(self.item.get_absolute_url(), f'/items/{self.item.pk}/')

    def test_default_status_is_acquired(self):
        item = Item.objects.create(name='Bare', acquisition_date=TODAY)
        self.assertEqual(item.status, Item.STATUS_ACQUIRED)

    def test_default_condition_is_unknown(self):
        item = Item.objects.create(name='Bare', acquisition_date=TODAY)
        self.assertEqual(item.condition, Item.CONDITION_UNKNOWN)

    def test_total_parts_cost_no_orders(self):
        self.assertEqual(self.item.total_parts_cost, 0)

    def test_total_parts_cost_counts_received_orders(self):
        PartOrder.objects.create(
            description='PSU', supplier=PartOrder.SUPPLIER_EBAY,
            order_date=LAST_WEEK, total_cost=Decimal('15.00'),
            status=PartOrder.STATUS_RECEIVED, for_item=self.item,
        )
        PartOrder.objects.create(
            description='RAM', supplier=PartOrder.SUPPLIER_AMAZON,
            order_date=LAST_WEEK, total_cost=Decimal('10.00'),
            status=PartOrder.STATUS_RECEIVED, for_item=self.item,
        )
        self.assertEqual(self.item.total_parts_cost, Decimal('25.00'))

    def test_total_parts_cost_excludes_non_received(self):
        PartOrder.objects.create(
            description='PSU', supplier=PartOrder.SUPPLIER_EBAY,
            order_date=LAST_WEEK, total_cost=Decimal('15.00'),
            status=PartOrder.STATUS_ORDERED, for_item=self.item,
        )
        self.assertEqual(self.item.total_parts_cost, 0)

    def test_total_revenue_no_sales(self):
        self.assertEqual(self.item.total_revenue, 0)

    def test_total_revenue_sums_net_amounts(self):
        Sale.objects.create(
            item=self.item, sale_date=TODAY,
            sale_price=Decimal('50.00'), fees=Decimal('5.00'),
            platform=Sale.PLATFORM_EBAY,
        )
        Sale.objects.create(
            item=self.item, sale_date=TODAY,
            sale_price=Decimal('20.00'), fees=Decimal('2.00'),
            platform=Sale.PLATFORM_EBAY,
        )
        self.assertEqual(self.item.total_revenue, Decimal('63.00'))

    def test_profit_calculation(self):
        self.item.cost_basis = Decimal('5.00')
        self.item.save()
        PartOrder.objects.create(
            description='PSU', supplier=PartOrder.SUPPLIER_EBAY,
            order_date=LAST_WEEK, total_cost=Decimal('10.00'),
            status=PartOrder.STATUS_RECEIVED, for_item=self.item,
        )
        Sale.objects.create(
            item=self.item, sale_date=TODAY,
            sale_price=Decimal('50.00'), fees=Decimal('0.00'),
            platform=Sale.PLATFORM_EBAY,
        )
        self.assertEqual(self.item.profit, Decimal('35.00'))

    def test_ordering_newest_first(self):
        Item.objects.create(name='Older', acquisition_date=LAST_WEEK)
        newer = Item.objects.create(name='Newer', acquisition_date=TODAY)
        self.assertEqual(Item.objects.first().pk, newer.pk)


class PartModelTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Dell Desktop', acquisition_date=TODAY)
        self.part = Part.objects.create(name='512MB RAM', source_item=self.item)

    def test_str(self):
        self.assertEqual(str(self.part), '512MB RAM')

    def test_get_absolute_url(self):
        self.assertEqual(self.part.get_absolute_url(), f'/parts/{self.part.pk}/')

    def test_default_status_is_available(self):
        self.assertEqual(self.part.status, Part.STATUS_AVAILABLE)


class PartOrderModelTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Dell Desktop', acquisition_date=TODAY)
        self.order = PartOrder.objects.create(
            description='Replacement PSU', supplier=PartOrder.SUPPLIER_EBAY,
            order_date=LAST_WEEK, total_cost=Decimal('15.00'), for_item=self.item,
        )

    def test_str(self):
        self.assertEqual(str(self.order), 'Replacement PSU')

    def test_get_absolute_url(self):
        self.assertEqual(self.order.get_absolute_url(), f'/orders/{self.order.pk}/')

    def test_supplier_display_known_supplier(self):
        self.assertEqual(self.order.supplier_display, 'eBay')

    def test_supplier_display_amazon(self):
        self.order.supplier = PartOrder.SUPPLIER_AMAZON
        self.assertEqual(self.order.supplier_display, 'Amazon')

    def test_supplier_display_other_with_name(self):
        self.order.supplier = PartOrder.SUPPLIER_OTHER
        self.order.supplier_other = 'Newegg'
        self.assertEqual(self.order.supplier_display, 'Newegg')

    def test_supplier_display_other_without_name(self):
        self.order.supplier = PartOrder.SUPPLIER_OTHER
        self.order.supplier_other = ''
        self.assertEqual(self.order.supplier_display, 'Other')

    def test_default_status_is_ordered(self):
        self.assertEqual(self.order.status, PartOrder.STATUS_ORDERED)


class SaleModelTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Dell Desktop', acquisition_date=TODAY)
        self.sale = Sale.objects.create(
            item=self.item, sale_date=TODAY,
            sale_price=Decimal('50.00'), fees=Decimal('5.00'),
            platform=Sale.PLATFORM_EBAY,
        )

    def test_net_amount(self):
        self.assertEqual(self.sale.net_amount, Decimal('45.00'))

    def test_net_amount_zero_fees(self):
        self.sale.fees = Decimal('0.00')
        self.assertEqual(self.sale.net_amount, Decimal('50.00'))

    def test_str_with_item(self):
        self.assertIn('50.00', str(self.sale))

    def test_str_with_description_only(self):
        sale = Sale(description='GPU', sale_price=Decimal('30.00'))
        self.assertIn('GPU', str(sale))

    def test_str_fallback(self):
        sale = Sale(sale_price=Decimal('10.00'))
        self.assertIn('Sale', str(sale))

    def test_get_absolute_url(self):
        self.assertEqual(self.sale.get_absolute_url(), f'/sales/{self.sale.pk}/')


class AuctionModelTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Dell Desktop', acquisition_date=TODAY)
        self.auction = Auction.objects.create(
            item=self.item, title='Dell Dimension 8200',
            ebay_item_id='123456789',
            start_date=LAST_WEEK, end_date=TOMORROW,
        )

    def test_str(self):
        self.assertEqual(str(self.auction), 'Dell Dimension 8200')

    def test_get_absolute_url(self):
        self.assertEqual(self.auction.get_absolute_url(), f'/auctions/{self.auction.pk}/')

    def test_is_active_when_active(self):
        self.assertTrue(self.auction.is_active)

    def test_is_active_false_when_ended_sold(self):
        self.auction.status = Auction.STATUS_ENDED_SOLD
        self.assertFalse(self.auction.is_active)

    def test_is_active_false_when_cancelled(self):
        self.auction.status = Auction.STATUS_CANCELLED
        self.assertFalse(self.auction.is_active)

    def test_ebay_url_with_id(self):
        self.assertEqual(self.auction.ebay_url, 'https://www.ebay.com/itm/123456789')

    def test_ebay_url_without_id(self):
        self.auction.ebay_item_id = ''
        self.assertIsNone(self.auction.ebay_url)

    def test_default_status_is_active(self):
        self.assertEqual(self.auction.status, Auction.STATUS_ACTIVE)


class ModelNoteModelTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Computer')
        self.note = ModelNote.objects.create(
            make='Dell', model='Dimension 8200',
            category=self.cat, notes='Uses PC800 RDRAM',
        )

    def test_str(self):
        self.assertEqual(str(self.note), 'Dell Dimension 8200')

    def test_get_absolute_url(self):
        self.assertEqual(self.note.get_absolute_url(), f'/model-notes/{self.note.pk}/')

    def test_unique_together_constraint(self):
        with self.assertRaises(IntegrityError):
            ModelNote.objects.create(make='Dell', model='Dimension 8200', notes='Dup')

    def test_ordering_by_make_then_model(self):
        ModelNote.objects.create(make='HP', model='Pavilion', notes='...')
        ModelNote.objects.create(make='Apple', model='iMac', notes='...')
        makes = list(ModelNote.objects.values_list('make', flat=True))
        self.assertEqual(makes, sorted(makes))
