from django.test import TestCase
from inventory.templatetags.inventory_tags import get_item, currency


class GetItemFilterTest(TestCase):
    def test_returns_value_for_existing_key(self):
        self.assertEqual(get_item({'acquired': 5}, 'acquired'), 5)

    def test_returns_zero_for_missing_key(self):
        self.assertEqual(get_item({'acquired': 5}, 'missing'), 0)

    def test_works_with_empty_dict(self):
        self.assertEqual(get_item({}, 'anything'), 0)


class CurrencyFilterTest(TestCase):
    def test_formats_integer(self):
        self.assertEqual(currency(50), '$50.00')

    def test_formats_decimal_string(self):
        self.assertEqual(currency('45.5'), '$45.50')

    def test_formats_large_number_with_comma(self):
        self.assertEqual(currency(1234.56), '$1,234.56')

    def test_returns_zero_for_none(self):
        self.assertEqual(currency(None), '$0.00')

    def test_returns_zero_for_invalid_string(self):
        self.assertEqual(currency('not-a-number'), '$0.00')

    def test_formats_zero(self):
        self.assertEqual(currency(0), '$0.00')
