"""Public previews use in-memory Figma samples (0 DB queries/writes) and never leak another store's data."""
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.home.models import Customer, Product, SalesTransaction
from apps.home.services import checkout, create_customer, create_product, current_store


class LandingPageSmokeTests(TestCase):
    def test_public_routes_and_account_links(self):
        for route in ('/', '/welcome/'):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'landing/landing.html')
            for name in ('login:login', 'register:register'):
                self.assertContains(response, f'href="{reverse(name)}"')
            for anchor in ('ledger-demo', 'inventory-story', 'daily-overview', 'faq'):
                self.assertContains(response, f'href="#{anchor}"')

    def test_anonymous_preview_renders_figma_sample_without_db_queries_or_writes(self):
        before = (Customer.objects.count(), Product.objects.count(), SalesTransaction.objects.count())
        with self.assertNumQueries(0):
            response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Walang laman sa simula ang bagong account.')
        self.assertContains(response, 'Halimbawang tala lamang')
        for sample in (
            '+₱150.00', '3 araw na lang', 'Aling Rosa', 'Bigas', '₱250.00',
            '-₱150.00', '₱200.00', 'Pancit Canton', 'Sardinas', '3 tala',
            '₱470.00', '₱270.00',
        ):
            self.assertContains(response, sample)
        self.assertNotContains(response, '>—<')
        self.assertEqual(before, (Customer.objects.count(), Product.objects.count(), SalesTransaction.objects.count()))

    def test_public_stock_order_toggle_reorders_sample_batches_and_handles_invalid_param(self):
        with self.assertNumQueries(0):
            arrival = self.client.get('/?order=arrival')
        self.assertEqual(arrival.status_code, 200)
        self.assertContains(arrival, 'BT-2026-072 · Estante B-2')
        self.assertContains(arrival, 'Unahin ang unang dumating na batch')
        self.assertContains(arrival, 'data-stock-order="arrival" aria-pressed="true"')

        with self.assertNumQueries(0):
            fallback = self.client.get('/?order=invalid')
        self.assertEqual(fallback.status_code, 200)
        self.assertContains(fallback, 'BT-2026-081 · Estante A-1')
        self.assertContains(fallback, 'Unahin ang pinakamalapit na expiry')
        self.assertContains(fallback, 'data-stock-order="expiry" aria-pressed="true"')

    def test_public_dashboard_preview_uses_sample_data_without_queries_and_sameorigin_header(self):
        with self.assertNumQueries(0):
            response = self.client.get(reverse('landing:dashboard_preview'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Frame-Options'], 'SAMEORIGIN')
        self.assertTemplateUsed(response, 'home/home.html')
        for sample in ('Aling Nena', '₱1,620.00', '₱1,450.00', 'Pancit Canton', 'Aling Rosa', 'Mang Ben'):
            self.assertContains(response, sample)
        self.assertNotContains(response, 'A fresh page for today.')
        self.assertNotContains(response, 'Demo Customer')

    def test_authenticated_preview_uses_only_the_current_stores_saved_records(self):
        owner = get_user_model().objects.create_user(username='preview-owner')
        other = get_user_model().objects.create_user(username='another-owner')
        store, other_store = current_store(owner), current_store(other)
        store.store_name = 'My saved shop'
        store.save()
        customer = create_customer(store, dict(name='My saved customer', credit_limit=Decimal('500')))
        create_customer(other_store, dict(name='Private other customer', credit_limit=Decimal('500')))
        product = create_product(store, dict(name='My saved product', category_name='My category',
            unit='pc', selling_price=Decimal('17'), cost_price=Decimal('9'),
            low_stock_threshold=1, has_expiry=False, stock_quantity=5))
        create_product(other_store, dict(name='Private other product', unit='pc',
            selling_price=Decimal('99'), cost_price=Decimal('50'), low_stock_threshold=1,
            has_expiry=False, stock_quantity=4))
        checkout(store, {'token': str(uuid4()), 'payment_method': 'Cash', 'cash_tendered': '20',
            'items': [{'product_id': product.pk, 'quantity': 1}]})
        self.client.force_login(owner)
        before = (Customer.objects.count(), Product.objects.count(), SalesTransaction.objects.count())
        response = self.client.get('/')
        dashboard = self.client.get(reverse('landing:dashboard_preview'))
        self.assertContains(dashboard, store.store_name)
        self.assertContains(dashboard, '₱17.00')
        self.assertNotContains(dashboard, 'Private other')
        self.assertNotContains(dashboard, 'Aling Nena')
        self.assertContains(response, customer.name)
        self.assertContains(response, product.name)
        self.assertContains(response, '₱17.00')
        self.assertNotContains(response, 'Private other')
        self.assertNotContains(response, 'Aling Rosa')
        self.assertEqual(before, (Customer.objects.count(), Product.objects.count(), SalesTransaction.objects.count()))

    def test_empty_authenticated_store_has_no_example_rows(self):
        owner = get_user_model().objects.create_user(username='empty-preview')
        self.client.force_login(owner)
        response = self.client.get('/')
        self.assertContains(response, '₱0.00')
        self.assertNotContains(response, 'Aling Rosa')
        self.assertEqual(current_store(owner).products.count(), 0)

    def test_dashboard_still_requires_login(self):
        self.assertEqual(reverse('home:index'), '/home/')
        self.assertRedirects(self.client.get('/home/'), '/login/?next=/home/', fetch_redirect_response=False)

    def test_authentication_templates_and_controls_are_retained_and_consistent(self):
        for route in ('/login/', '/register/'):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'id="back-to-landing-btn"')
            self.assertContains(response, 'class="container-auth"')
            self.assertContains(response, 'imgPhosphorStorefront.svg')
            self.assertContains(response, 'cy="12" r="3"')
            self.assertNotContains(response, 'cy="3"')
        login_page = self.client.get('/login/')
        self.assertNotContains(login_page, 'automate Singilan')
        step2_error = self.client.post('/register/', {
            'store_name': 'Sari Store Test',
            'owner_name': 'Maria Clara',
            'phone': '09171234567',
            'password': 'Strong#Password2026',
            'confirm_password': 'Mismatch#Password2026',
        })
        self.assertEqual(step2_error.status_code, 200)
        self.assertContains(step2_error, 'data-has-step2-errors="true"')
        self.assertContains(step2_error, 'Sari Store Test')
        self.assertContains(step2_error, 'Passwords do not match.')
