from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from inventory.models import Category, Item, Part, PartOrder, Sale, ModelNote, Auction
from inventory.test_fixtures import InventoryFixtures, TODAY, TOMORROW, LAST_WEEK


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(reverse('inventory:dashboard')).status_code, 200)

    def test_context_contains_active_item_count(self):
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertGreaterEqual(response.context['active_item_count'], 1)

    def test_context_contains_active_auctions(self):
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertEqual(response.context['active_auction_count'], 1)

    def test_total_revenue_is_net(self):
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertEqual(response.context['total_revenue'], Decimal('40.00'))

    def test_sold_item_excluded_from_active_count(self):
        self.item.status = Item.STATUS_SOLD
        self.item.save()
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertEqual(response.context['active_item_count'], 0)

    def test_status_counts_in_context(self):
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertIn('status_counts', response.context)
        self.assertEqual(response.context['status_counts'][Item.STATUS_ACQUIRED], 1)


# ── Items ─────────────────────────────────────────────────────────────────────

class ItemListViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:item_list')

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_lists_all_items(self):
        self.assertIn(self.item, self.client.get(self.url).context['items'])

    def test_search_by_make(self):
        self.assertIn(self.item, self.client.get(self.url, {'q': 'Dell'}).context['items'])

    def test_search_by_model(self):
        self.assertIn(self.item, self.client.get(self.url, {'q': 'Dimension'}).context['items'])

    def test_search_by_source(self):
        self.assertIn(self.item, self.client.get(self.url, {'q': 'Main St'}).context['items'])

    def test_search_no_results(self):
        self.assertNotIn(self.item, self.client.get(self.url, {'q': 'Commodore'}).context['items'])

    def test_filter_by_status_match(self):
        self.assertIn(self.item, self.client.get(self.url, {'status': Item.STATUS_ACQUIRED}).context['items'])

    def test_filter_by_status_no_match(self):
        self.assertNotIn(self.item, self.client.get(self.url, {'status': Item.STATUS_SOLD}).context['items'])

    def test_filter_by_category(self):
        self.assertIn(self.item, self.client.get(self.url, {'category': self.category.pk}).context['items'])

    def test_htmx_returns_table_partial(self):
        r = self.client.get(self.url, HTTP_HX_REQUEST='true')
        self.assertTemplateUsed(r, 'inventory/items/_table.html')
        self.assertTemplateNotUsed(r, 'inventory/base.html')

    def test_normal_request_uses_full_page(self):
        self.assertTemplateUsed(self.client.get(self.url), 'inventory/items/list.html')


class ItemDetailViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()

    def test_get_returns_200(self):
        self.assertEqual(
            self.client.get(reverse('inventory:item_detail', args=[self.item.pk])).status_code, 200
        )

    def test_404_for_nonexistent(self):
        self.assertEqual(
            self.client.get(reverse('inventory:item_detail', args=[99999])).status_code, 404
        )

    def test_related_parts_in_context(self):
        r = self.client.get(reverse('inventory:item_detail', args=[self.item.pk]))
        self.assertIn(self.part, r.context['harvested_parts'])

    def test_related_order_in_context(self):
        r = self.client.get(reverse('inventory:item_detail', args=[self.item.pk]))
        self.assertIn(self.order, r.context['orders'])

    def test_related_sale_in_context(self):
        r = self.client.get(reverse('inventory:item_detail', args=[self.item.pk]))
        self.assertIn(self.sale, r.context['sales'])

    def test_related_auction_in_context(self):
        r = self.client.get(reverse('inventory:item_detail', args=[self.item.pk]))
        self.assertIn(self.auction, r.context['auctions'])


class ItemCreateViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:item_create')

    def _data(self, **kw):
        d = {
            'name': 'New Item', 'make': 'HP', 'model': 'Pavilion',
            'acquisition_date': str(TODAY),
            'condition': Item.CONDITION_UNKNOWN,
            'status': Item.STATUS_ACQUIRED,
            'cost_basis': '0.00', 'notes': '',
        }
        d.update(kw)
        return d

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_get_with_date_param(self):
        self.assertEqual(self.client.get(self.url, {'date': str(TODAY)}).status_code, 200)

    def test_post_valid_creates_item_and_redirects(self):
        r = self.client.post(self.url, self._data())
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Item.objects.filter(name='New Item').exists())

    def test_post_invalid_rerenders_200(self):
        r = self.client.post(self.url, self._data(name=''))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Item.objects.filter(make='HP', model='Pavilion').exists())


class ItemEditViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:item_edit', args=[self.item.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_valid_updates_status(self):
        self.client.post(self.url, {
            'name': 'Dell Desktop', 'make': 'Dell', 'model': 'Dimension 8200',
            'acquisition_date': str(TODAY), 'condition': Item.CONDITION_WORKING,
            'status': Item.STATUS_TESTING, 'cost_basis': '0.00', 'notes': '',
        })
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.STATUS_TESTING)

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, {'name': ''}).status_code, 200)


class ItemDeleteViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:item_delete', args=[self.item.pk])

    def test_get_returns_confirmation_page(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_deletes_and_redirects(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())


class ItemStatusUpdateViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:item_status_update', args=[self.item.pk])

    def test_post_valid_status_updates_item(self):
        self.client.post(self.url, {'status': Item.STATUS_TESTING})
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.STATUS_TESTING)

    def test_post_invalid_status_is_ignored(self):
        self.client.post(self.url, {'status': 'not_real'})
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.STATUS_ACQUIRED)

    def test_get_returns_badge_without_update(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.STATUS_ACQUIRED)

    def test_returns_status_badge_partial(self):
        r = self.client.post(self.url, {'status': Item.STATUS_REPAIRING})
        self.assertTemplateUsed(r, 'inventory/items/_status_badge.html')


# ── Parts ─────────────────────────────────────────────────────────────────────

class PartListViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:part_list')

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_search_by_name(self):
        self.assertIn(self.part, self.client.get(self.url, {'q': 'RAM'}).context['parts'])

    def test_search_by_description(self):
        self.assertIn(self.part, self.client.get(self.url, {'q': 'RDRAM'}).context['parts'])

    def test_filter_by_status(self):
        self.assertIn(
            self.part,
            self.client.get(self.url, {'status': Part.STATUS_AVAILABLE}).context['parts']
        )

    def test_htmx_returns_partial(self):
        self.assertTemplateUsed(
            self.client.get(self.url, HTTP_HX_REQUEST='true'),
            'inventory/parts/_table.html'
        )


class PartDetailViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()

    def test_get_returns_200(self):
        self.assertEqual(
            self.client.get(reverse('inventory:part_detail', args=[self.part.pk])).status_code, 200
        )

    def test_404_for_nonexistent(self):
        self.assertEqual(
            self.client.get(reverse('inventory:part_detail', args=[99999])).status_code, 404
        )


class PartCreateViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:part_create')

    def _data(self, **kw):
        d = {
            'name': 'New Part', 'description': '', 'source_item': '',
            'used_in_item': '', 'condition': 'Good',
            'status': Part.STATUS_AVAILABLE, 'notes': '',
        }
        d.update(kw)
        return d

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_get_with_source_item_param(self):
        self.assertEqual(self.client.get(self.url, {'source_item': self.item.pk}).status_code, 200)

    def test_get_with_used_in_item_param(self):
        self.assertEqual(self.client.get(self.url, {'used_in_item': self.item.pk}).status_code, 200)

    def test_post_valid_creates_part(self):
        r = self.client.post(self.url, self._data())
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Part.objects.filter(name='New Part').exists())

    def test_post_with_next_redirects(self):
        next_url = reverse('inventory:item_detail', args=[self.item.pk])
        r = self.client.post(self.url + f'?next={next_url}', self._data(name='Redir Part'))
        self.assertRedirects(r, next_url)

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, self._data(name='')).status_code, 200)


class PartEditViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:part_edit', args=[self.part.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_valid_updates_status(self):
        self.client.post(self.url, {
            'name': '512MB RAM', 'description': '', 'source_item': self.item.pk,
            'used_in_item': '', 'condition': 'Good',
            'status': Part.STATUS_USED, 'notes': '',
        })
        self.part.refresh_from_db()
        self.assertEqual(self.part.status, Part.STATUS_USED)

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, {'name': ''}).status_code, 200)


class PartDeleteViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:part_delete', args=[self.part.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_deletes_part(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Part.objects.filter(pk=self.part.pk).exists())


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderListViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:order_list')

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_search_by_description(self):
        self.assertIn(self.order, self.client.get(self.url, {'q': 'PSU'}).context['orders'])

    def test_filter_by_status(self):
        self.assertIn(
            self.order,
            self.client.get(self.url, {'status': PartOrder.STATUS_ORDERED}).context['orders']
        )

    def test_htmx_returns_partial(self):
        self.assertTemplateUsed(
            self.client.get(self.url, HTTP_HX_REQUEST='true'),
            'inventory/orders/_table.html'
        )


class OrderDetailViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()

    def test_get_returns_200(self):
        self.assertEqual(
            self.client.get(reverse('inventory:order_detail', args=[self.order.pk])).status_code, 200
        )

    def test_404_for_nonexistent(self):
        self.assertEqual(
            self.client.get(reverse('inventory:order_detail', args=[99999])).status_code, 404
        )


class OrderCreateViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:order_create')

    def _data(self, **kw):
        d = {
            'description': 'New Order', 'supplier': PartOrder.SUPPLIER_EBAY,
            'supplier_other': '', 'order_date': str(TODAY),
            'expected_date': '', 'received_date': '',
            'status': PartOrder.STATUS_ORDERED, 'tracking_number': '',
            'total_cost': '20.00', 'for_item': '', 'notes': '',
        }
        d.update(kw)
        return d

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_get_with_for_item_param(self):
        self.assertEqual(self.client.get(self.url, {'for_item': self.item.pk}).status_code, 200)

    def test_post_valid_creates_order(self):
        r = self.client.post(self.url, self._data())
        self.assertEqual(r.status_code, 302)
        self.assertTrue(PartOrder.objects.filter(description='New Order').exists())

    def test_post_with_next_redirects(self):
        next_url = reverse('inventory:item_detail', args=[self.item.pk])
        r = self.client.post(self.url + f'?next={next_url}', self._data(description='Redir Order'))
        self.assertRedirects(r, next_url)

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, self._data(description='')).status_code, 200)


class OrderEditViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:order_edit', args=[self.order.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_valid_updates_order(self):
        self.client.post(self.url, {
            'description': 'Updated PSU', 'supplier': PartOrder.SUPPLIER_AMAZON,
            'supplier_other': '', 'order_date': str(TODAY),
            'expected_date': '', 'received_date': '',
            'status': PartOrder.STATUS_SHIPPED, 'tracking_number': '1Z999',
            'total_cost': '18.00', 'for_item': self.item.pk, 'notes': '',
        })
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, PartOrder.STATUS_SHIPPED)
        self.assertEqual(self.order.tracking_number, '1Z999')

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, {'description': ''}).status_code, 200)


class OrderDeleteViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:order_delete', args=[self.order.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_deletes_order(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertFalse(PartOrder.objects.filter(pk=self.order.pk).exists())


class OrderStatusUpdateViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:order_status_update', args=[self.order.pk])

    def test_received_sets_received_date(self):
        self.assertIsNone(self.order.received_date)
        self.client.post(self.url, {'status': PartOrder.STATUS_RECEIVED})
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, PartOrder.STATUS_RECEIVED)
        self.assertIsNotNone(self.order.received_date)

    def test_received_does_not_overwrite_existing_date(self):
        self.order.received_date = LAST_WEEK
        self.order.save()
        self.client.post(self.url, {'status': PartOrder.STATUS_RECEIVED})
        self.order.refresh_from_db()
        self.assertEqual(self.order.received_date, LAST_WEEK)

    def test_shipped_does_not_set_received_date(self):
        self.client.post(self.url, {'status': PartOrder.STATUS_SHIPPED})
        self.order.refresh_from_db()
        self.assertIsNone(self.order.received_date)

    def test_invalid_status_is_ignored(self):
        self.client.post(self.url, {'status': 'bogus'})
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, PartOrder.STATUS_ORDERED)

    def test_returns_status_badge_partial(self):
        r = self.client.post(self.url, {'status': PartOrder.STATUS_SHIPPED})
        self.assertTemplateUsed(r, 'inventory/orders/_status_badge.html')


# ── Sales ─────────────────────────────────────────────────────────────────────

class SaleListViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:sale_list')

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_context_totals(self):
        r = self.client.get(self.url)
        self.assertEqual(r.context['gross'], Decimal('45.00'))
        self.assertEqual(r.context['fees'], Decimal('5.00'))
        self.assertEqual(r.context['net'], Decimal('40.00'))

    def test_filter_by_platform_match(self):
        self.assertIn(
            self.sale,
            self.client.get(self.url, {'platform': Sale.PLATFORM_EBAY}).context['sales']
        )

    def test_filter_by_platform_no_match(self):
        self.assertNotIn(
            self.sale,
            self.client.get(self.url, {'platform': Sale.PLATFORM_LOCAL}).context['sales']
        )

    def test_search_by_item_name(self):
        self.assertIn(self.sale, self.client.get(self.url, {'q': 'Dell'}).context['sales'])

    def test_htmx_returns_partial(self):
        self.assertTemplateUsed(
            self.client.get(self.url, HTTP_HX_REQUEST='true'),
            'inventory/sales/_table.html'
        )

    def test_empty_db_totals_are_zero(self):
        Sale.objects.all().delete()
        r = self.client.get(self.url)
        self.assertEqual(r.context['gross'], 0)
        self.assertEqual(r.context['net'], 0)


class SaleDetailViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()

    def test_get_returns_200(self):
        self.assertEqual(
            self.client.get(reverse('inventory:sale_detail', args=[self.sale.pk])).status_code, 200
        )

    def test_404_for_nonexistent(self):
        self.assertEqual(
            self.client.get(reverse('inventory:sale_detail', args=[99999])).status_code, 404
        )


class SaleCreateViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:sale_create')
        self.fresh_item = Item.objects.create(
            name='HP Laptop', acquisition_date=TODAY, status=Item.STATUS_LISTED
        )
        self.fresh_part = Part.objects.create(name='GPU', status=Part.STATUS_AVAILABLE)

    def _data(self, **kw):
        d = {
            'item': '', 'part': '', 'description': 'Misc sale',
            'sale_date': str(TODAY), 'sale_price': '30.00',
            'platform': Sale.PLATFORM_LOCAL, 'fees': '0.00', 'notes': '',
        }
        d.update(kw)
        return d

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_get_with_item_param(self):
        self.assertEqual(self.client.get(self.url, {'item': self.fresh_item.pk}).status_code, 200)

    def test_get_with_part_param(self):
        self.assertEqual(self.client.get(self.url, {'part': self.fresh_part.pk}).status_code, 200)

    def test_post_valid_creates_sale(self):
        r = self.client.post(self.url, self._data())
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Sale.objects.filter(description='Misc sale').exists())

    def test_post_marks_linked_item_sold(self):
        self.client.post(self.url, self._data(item=self.fresh_item.pk, description=''))
        self.fresh_item.refresh_from_db()
        self.assertEqual(self.fresh_item.status, Item.STATUS_SOLD)

    def test_post_marks_linked_part_sold(self):
        self.client.post(self.url, self._data(part=self.fresh_part.pk))
        self.fresh_part.refresh_from_db()
        self.assertEqual(self.fresh_part.status, Part.STATUS_SOLD)

    def test_post_already_sold_item_does_not_error(self):
        self.fresh_item.status = Item.STATUS_SOLD
        self.fresh_item.save()
        r = self.client.post(self.url, self._data(item=self.fresh_item.pk, description=''))
        self.assertEqual(r.status_code, 302)

    def test_post_with_next_redirects(self):
        next_url = reverse('inventory:item_detail', args=[self.item.pk])
        r = self.client.post(self.url + f'?next={next_url}', self._data(description='Next'))
        self.assertRedirects(r, next_url)

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, self._data(sale_price='')).status_code, 200)


class SaleEditViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:sale_edit', args=[self.sale.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_valid_updates_price(self):
        self.client.post(self.url, {
            'item': self.item.pk, 'part': '', 'description': '',
            'sale_date': str(TODAY), 'sale_price': '60.00',
            'platform': Sale.PLATFORM_FACEBOOK, 'fees': '0.00', 'notes': '',
        })
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.sale_price, Decimal('60.00'))

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, {'sale_price': ''}).status_code, 200)


class SaleDeleteViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:sale_delete', args=[self.sale.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_deletes_sale(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Sale.objects.filter(pk=self.sale.pk).exists())


# ── Auctions ──────────────────────────────────────────────────────────────────

class AuctionListViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:auction_list')

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_search_by_title(self):
        self.assertIn(
            self.auction,
            self.client.get(self.url, {'q': 'Dell'}).context['auctions']
        )

    def test_search_by_ebay_id(self):
        self.assertIn(
            self.auction,
            self.client.get(self.url, {'q': '123456789'}).context['auctions']
        )

    def test_filter_by_active_status(self):
        self.assertIn(
            self.auction,
            self.client.get(self.url, {'status': Auction.STATUS_ACTIVE}).context['auctions']
        )

    def test_htmx_returns_partial(self):
        self.assertTemplateUsed(
            self.client.get(self.url, HTTP_HX_REQUEST='true'),
            'inventory/auctions/_table.html'
        )


class AuctionDetailViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()

    def test_get_returns_200(self):
        self.assertEqual(
            self.client.get(reverse('inventory:auction_detail', args=[self.auction.pk])).status_code, 200
        )

    def test_404_for_nonexistent(self):
        self.assertEqual(
            self.client.get(reverse('inventory:auction_detail', args=[99999])).status_code, 404
        )


class AuctionCreateViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:auction_create')

    def _data(self, **kw):
        d = {
            'title': 'Test Auction Listing', 'item': self.item.pk, 'part': '',
            'ebay_item_id': '987654321', 'starting_bid': '4.99', 'buy_it_now': '',
            'start_date': str(TODAY), 'end_date': str(TOMORROW),
            'status': Auction.STATUS_ACTIVE, 'final_price': '', 'notes': '',
        }
        d.update(kw)
        return d

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_get_with_item_param(self):
        self.assertEqual(self.client.get(self.url, {'item': self.item.pk}).status_code, 200)

    def test_get_with_part_param(self):
        self.assertEqual(self.client.get(self.url, {'part': self.part.pk}).status_code, 200)

    def test_post_valid_creates_auction(self):
        r = self.client.post(self.url, self._data())
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Auction.objects.filter(title='Test Auction Listing').exists())

    def test_post_with_next_redirects(self):
        next_url = reverse('inventory:item_detail', args=[self.item.pk])
        r = self.client.post(self.url + f'?next={next_url}', self._data(title='Redir Auction'))
        self.assertRedirects(r, next_url)

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, self._data(title='')).status_code, 200)


class AuctionEditViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:auction_edit', args=[self.auction.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_valid_updates_status(self):
        self.client.post(self.url, {
            'title': 'Updated Title', 'item': self.item.pk, 'part': '',
            'ebay_item_id': '123456789', 'starting_bid': '9.99', 'buy_it_now': '',
            'start_date': str(LAST_WEEK), 'end_date': str(TOMORROW),
            'status': Auction.STATUS_ENDED_UNSOLD, 'final_price': '', 'notes': '',
        })
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.status, Auction.STATUS_ENDED_UNSOLD)

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, {'title': ''}).status_code, 200)


class AuctionDeleteViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:auction_delete', args=[self.auction.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_deletes_auction(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Auction.objects.filter(pk=self.auction.pk).exists())


class AuctionConvertViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.fresh_item = Item.objects.create(
            name='HP Laptop', acquisition_date=TODAY, status=Item.STATUS_LISTED
        )
        self.auction.item = self.fresh_item
        self.auction.final_price = Decimal('55.00')
        self.auction.save()
        self.url = reverse('inventory:auction_convert', args=[self.auction.pk])

    def _data(self, **kw):
        d = {
            'item': self.fresh_item.pk, 'part': '',
            'description': self.auction.title,
            'sale_date': str(TODAY), 'sale_price': '55.00',
            'platform': Sale.PLATFORM_EBAY, 'fees': '6.00', 'notes': '',
        }
        d.update(kw)
        return d

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertTemplateUsed(
            self.client.get(self.url), 'inventory/auctions/convert.html'
        )

    def test_get_prefills_final_price(self):
        r = self.client.get(self.url)
        self.assertEqual(str(r.context['form'].initial.get('sale_price')), '55.00')

    def test_get_prefills_item(self):
        r = self.client.get(self.url)
        self.assertEqual(r.context['form'].initial.get('item'), self.fresh_item.pk)

    def test_post_creates_sale(self):
        self.client.post(self.url, self._data())
        self.assertTrue(Sale.objects.filter(sale_price=Decimal('55.00')).exists())

    def test_post_marks_auction_ended_sold(self):
        self.client.post(self.url, self._data())
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.status, Auction.STATUS_ENDED_SOLD)

    def test_post_links_auction_to_sale(self):
        self.client.post(self.url, self._data())
        self.auction.refresh_from_db()
        self.assertIsNotNone(self.auction.sale_id)

    def test_post_marks_item_sold(self):
        self.client.post(self.url, self._data())
        self.fresh_item.refresh_from_db()
        self.assertEqual(self.fresh_item.status, Item.STATUS_SOLD)

    def test_post_marks_part_sold(self):
        fresh_part = Part.objects.create(name='GPU', status=Part.STATUS_AVAILABLE)
        self.auction.item = None
        self.auction.part = fresh_part
        self.auction.save()
        self.client.post(self.url, self._data(item='', part=fresh_part.pk))
        fresh_part.refresh_from_db()
        self.assertEqual(fresh_part.status, Part.STATUS_SOLD)

    def test_post_does_not_overwrite_existing_final_price(self):
        self.client.post(self.url, self._data(sale_price='70.00'))
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.final_price, Decimal('55.00'))

    def test_post_sets_final_price_when_none(self):
        self.auction.final_price = None
        self.auction.save()
        self.client.post(self.url, self._data(sale_price='42.00'))
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.final_price, Decimal('42.00'))

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, self._data(sale_price='')).status_code, 200)

    def test_already_converted_redirects_to_existing_sale(self):
        existing_sale = Sale.objects.create(
            sale_date=TODAY, sale_price=Decimal('55.00'), platform=Sale.PLATFORM_EBAY,
        )
        self.auction.sale = existing_sale
        self.auction.save()
        r = self.client.get(self.url)
        self.assertRedirects(r, existing_sale.get_absolute_url())


# ── Model Notes ───────────────────────────────────────────────────────────────

class ModelNoteListViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:modelnote_list')

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_search_by_make(self):
        self.assertIn(self.model_note, self.client.get(self.url, {'q': 'Dell'}).context['notes'])

    def test_search_by_note_content(self):
        self.assertIn(self.model_note, self.client.get(self.url, {'q': 'RDRAM'}).context['notes'])

    def test_filter_by_category(self):
        self.assertIn(
            self.model_note,
            self.client.get(self.url, {'category': self.category.pk}).context['notes']
        )

    def test_htmx_returns_partial(self):
        self.assertTemplateUsed(
            self.client.get(self.url, HTTP_HX_REQUEST='true'),
            'inventory/model_notes/_table.html'
        )


class ModelNoteDetailViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()

    def test_get_returns_200(self):
        self.assertEqual(
            self.client.get(reverse('inventory:modelnote_detail', args=[self.model_note.pk])).status_code, 200
        )

    def test_related_items_in_context(self):
        r = self.client.get(reverse('inventory:modelnote_detail', args=[self.model_note.pk]))
        self.assertIn(self.item, r.context['related_items'])

    def test_404_for_nonexistent(self):
        self.assertEqual(
            self.client.get(reverse('inventory:modelnote_detail', args=[99999])).status_code, 404
        )


class ModelNoteCreateViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:modelnote_create')

    def _data(self, **kw):
        d = {
            'make': 'HP', 'model': 'Pavilion dv7',
            'category': self.category.pk, 'notes': 'Common hinge failure.',
        }
        d.update(kw)
        return d

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_get_with_make_model_params(self):
        self.assertEqual(
            self.client.get(self.url, {'make': 'HP', 'model': 'Elitebook'}).status_code, 200
        )

    def test_post_valid_creates_note(self):
        r = self.client.post(self.url, self._data())
        self.assertEqual(r.status_code, 302)
        self.assertTrue(ModelNote.objects.filter(make='HP', model='Pavilion dv7').exists())

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, self._data(make='')).status_code, 200)


class ModelNoteEditViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:modelnote_edit', args=[self.model_note.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_valid_updates_notes(self):
        self.client.post(self.url, {
            'make': 'Dell', 'model': 'Dimension 8200',
            'category': self.category.pk, 'notes': 'Updated notes.',
        })
        self.model_note.refresh_from_db()
        self.assertEqual(self.model_note.notes, 'Updated notes.')

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, {'make': ''}).status_code, 200)


class ModelNoteDeleteViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:modelnote_delete', args=[self.model_note.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_deletes_note(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertFalse(ModelNote.objects.filter(pk=self.model_note.pk).exists())


# ── Categories ────────────────────────────────────────────────────────────────

class CategoryListViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()

    def test_get_returns_200(self):
        self.assertEqual(
            self.client.get(reverse('inventory:category_list')).status_code, 200
        )

    def test_lists_categories(self):
        r = self.client.get(reverse('inventory:category_list'))
        self.assertIn(self.category, r.context['categories'])


class CategoryCreateViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:category_create')

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_valid_creates_category(self):
        r = self.client.post(self.url, {'name': 'TV'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Category.objects.filter(name='TV').exists())

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, {'name': ''}).status_code, 200)


class CategoryEditViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.url = reverse('inventory:category_edit', args=[self.category.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_valid_updates_name(self):
        self.client.post(self.url, {'name': 'Desktop Computer'})
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Desktop Computer')

    def test_post_invalid_rerenders_200(self):
        self.assertEqual(self.client.post(self.url, {'name': ''}).status_code, 200)


class CategoryDeleteViewTest(InventoryFixtures, TestCase):
    def setUp(self):
        self.make_fixtures()
        self.extra = Category.objects.create(name='Printer')
        self.url = reverse('inventory:category_delete', args=[self.extra.pk])

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_deletes_category(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Category.objects.filter(pk=self.extra.pk).exists())
