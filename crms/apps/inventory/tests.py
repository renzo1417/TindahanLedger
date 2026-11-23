from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.home.services import create_product, current_store


class InventoryPresentationTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='inventory-review')
        self.store = current_store(self.owner)
        self.client.force_login(self.owner)

    def test_expired_stock_is_flagged_and_filters_use_saved_batches(self):
        product = create_product(self.store, {
            'name': 'Saved dated product', 'unit': 'box', 'selling_price': Decimal('20'),
            'cost_price': Decimal('12'), 'stock_quantity': 6, 'low_stock_threshold': 1,
            'has_expiry': True, 'expiry_date': timezone.localdate() + timedelta(days=10),
        })
        batch = product.batches.get()
        batch.expiry_date = timezone.localdate() - timedelta(days=1)
        batch.save()
        response = self.client.get('/inventory/?filter=expired')
        self.assertContains(response, product.name)
        self.assertContains(response, 'Expired batch')
        self.assertEqual(response.context['expired_count'], 1)
        self.assertEqual(response.context['attention_count'], 1)
        self.assertEqual(response.context['inventory_cost'], Decimal('72'))
        self.assertNotContains(self.client.get('/inventory/?filter=expiring_soon'), product.name)

    def test_ordinary_empty_store_has_zero_counts_and_no_rows(self):
        response = self.client.get('/inventory/')
        self.assertContains(response, 'No paninda found.')
        for key in ('product_count', 'low_stock_count', 'expired_count', 'expiring_count', 'attention_count'):
            self.assertEqual(response.context[key], 0)
        self.assertEqual(self.store.products.count(), 0)
