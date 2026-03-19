from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase

from inventory.models import Category, Item, Part, PartOrder, Sale, ModelNote, Auction
from inventory.forms import (
    ItemForm, PartForm, PartOrderForm, SaleForm,
    ModelNoteForm, CategoryForm, AuctionForm,
)

TODAY = date.today()
TOMORROW = TODAY + timedelta(days=1)
LAST_WEEK = TODAY - timedelta(days=7)


class ItemFormTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Computer')

    def _valid_data(self, **overrides):
        data = {
            'name': 'Dell Desktop', 'make': 'Dell', 'model': 'Dimension 8200',
            'category': self.cat.pk, 'acquisition_date': str(TODAY),
            'acquisition_source': '123 Main St',
            'condition': Item.CONDITION_NOT_WORKING,
            'status': Item.STATUS_ACQUIRED,
            'cost_basis': '0.00', 'notes': '',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        self.assertTrue(ItemForm(data=self._valid_data()).is_valid())

    def test_missing_name_is_invalid(self):
        form = ItemForm(data=self._valid_data(name=''))
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_missing_acquisition_date_is_invalid(self):
        form = ItemForm(data=self._valid_data(acquisition_date=''))
        self.assertFalse(form.is_valid())

    def test_category_is_optional(self):
        self.assertTrue(ItemForm(data=self._valid_data(category='')).is_valid())

    def test_form_has_crispy_helper(self):
        self.assertIsNotNone(ItemForm().helper)


class PartFormTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Dell Desktop', acquisition_date=TODAY)

    def _valid_data(self, **overrides):
        data = {
            'name': '512MB RAM', 'description': 'PC800',
            'source_item': self.item.pk, 'used_in_item': '',
            'condition': 'Good', 'status': Part.STATUS_AVAILABLE, 'notes': '',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        self.assertTrue(PartForm(data=self._valid_data()).is_valid())

    def test_missing_name_is_invalid(self):
        self.assertFalse(PartForm(data=self._valid_data(name='')).is_valid())

    def test_form_has_crispy_helper(self):
        self.assertIsNotNone(PartForm().helper)


class PartOrderFormTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Dell Desktop', acquisition_date=TODAY)

    def _valid_data(self, **overrides):
        data = {
            'description': 'Replacement PSU', 'supplier': PartOrder.SUPPLIER_EBAY,
            'supplier_other': '', 'order_date': str(TODAY),
            'expected_date': '', 'received_date': '',
            'status': PartOrder.STATUS_ORDERED, 'tracking_number': '',
            'total_cost': '15.00', 'for_item': '', 'notes': '',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        self.assertTrue(PartOrderForm(data=self._valid_data()).is_valid())

    def test_missing_description_is_invalid(self):
        self.assertFalse(PartOrderForm(data=self._valid_data(description='')).is_valid())

    def test_missing_total_cost_is_invalid(self):
        self.assertFalse(PartOrderForm(data=self._valid_data(total_cost='')).is_valid())

    def test_for_item_is_optional(self):
        self.assertTrue(PartOrderForm(data=self._valid_data(for_item='')).is_valid())

    def test_form_has_crispy_helper(self):
        self.assertIsNotNone(PartOrderForm().helper)


class SaleFormTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Dell Desktop', acquisition_date=TODAY)

    def _valid_data(self, **overrides):
        data = {
            'item': self.item.pk, 'part': '', 'description': '',
            'sale_date': str(TODAY), 'sale_price': '45.00',
            'platform': Sale.PLATFORM_EBAY, 'fees': '5.00', 'notes': '',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        self.assertTrue(SaleForm(data=self._valid_data()).is_valid())

    def test_missing_sale_date_is_invalid(self):
        self.assertFalse(SaleForm(data=self._valid_data(sale_date='')).is_valid())

    def test_missing_sale_price_is_invalid(self):
        self.assertFalse(SaleForm(data=self._valid_data(sale_price='')).is_valid())

    def test_item_and_part_both_optional(self):
        self.assertTrue(SaleForm(data=self._valid_data(item='', description='GPU')).is_valid())

    def test_form_has_crispy_helper(self):
        self.assertIsNotNone(SaleForm().helper)


class ModelNoteFormTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Computer')

    def _valid_data(self, **overrides):
        data = {
            'make': 'Dell', 'model': 'Dimension 8200',
            'category': self.cat.pk, 'notes': 'Uses PC800 RDRAM',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        self.assertTrue(ModelNoteForm(data=self._valid_data()).is_valid())

    def test_missing_make_is_invalid(self):
        self.assertFalse(ModelNoteForm(data=self._valid_data(make='')).is_valid())

    def test_missing_notes_is_invalid(self):
        self.assertFalse(ModelNoteForm(data=self._valid_data(notes='')).is_valid())

    def test_form_has_crispy_helper(self):
        self.assertIsNotNone(ModelNoteForm().helper)


class CategoryFormTest(TestCase):
    def test_valid_form(self):
        self.assertTrue(CategoryForm(data={'name': 'TV'}).is_valid())

    def test_missing_name_is_invalid(self):
        self.assertFalse(CategoryForm(data={'name': ''}).is_valid())

    def test_form_has_crispy_helper(self):
        self.assertIsNotNone(CategoryForm().helper)


class AuctionFormTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Dell Desktop', acquisition_date=TODAY)

    def _valid_data(self, **overrides):
        data = {
            'title': 'Dell Dimension 8200 Desktop', 'item': self.item.pk, 'part': '',
            'ebay_item_id': '123456789', 'starting_bid': '9.99', 'buy_it_now': '',
            'start_date': str(TODAY), 'end_date': str(TOMORROW),
            'status': Auction.STATUS_ACTIVE, 'final_price': '', 'notes': '',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        self.assertTrue(AuctionForm(data=self._valid_data()).is_valid())

    def test_missing_title_is_invalid(self):
        self.assertFalse(AuctionForm(data=self._valid_data(title='')).is_valid())

    def test_missing_end_date_is_invalid(self):
        self.assertFalse(AuctionForm(data=self._valid_data(end_date='')).is_valid())

    def test_item_is_optional(self):
        self.assertTrue(AuctionForm(data=self._valid_data(item='')).is_valid())

    def test_form_has_crispy_helper(self):
        self.assertIsNotNone(AuctionForm().helper)
