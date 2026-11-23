"""Public previews must never invent records or leak another store's data."""
from decimal import Decimal
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from apps.home.models import Customer, Product, SalesTransaction
from apps.home.services import current_store, create_customer, create_product, checkout


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

    def test_anonymous_preview_neither_queries_nor_invents_business_records(self):
        before = (Customer.objects.count(), Product.objects.count(), SalesTransaction.objects.count())
        with self.assertNumQueries(0):
            response = self.client.get('/')
        self.assertContains(response, 'New accounts start empty.')
        self.assertContains(response, 'Walang customer data sa public preview')
        for sample in ('Aling Rosa', 'Aling Nena', 'Pancit Canton', '470.00', '270.00', 'overview.webp'):
            self.assertNotContains(response, sample)
        self.assertEqual(before, (Customer.objects.count(), Product.objects.count(), SalesTransaction.objects.count()))

    def test_public_dashboard_preview_is_empty_and_can_only_be_embedded_on_this_site(self):
        with self.assertNumQueries(0):
            response = self.client.get(reverse('landing:dashboard_preview'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Frame-Options'], 'SAMEORIGIN')
        self.assertTemplateUsed(response, 'home/home.html')
        self.assertContains(response, 'Your tindahan')
        self.assertContains(response, '₱0.00')
        self.assertContains(response, 'A fresh page for today.')
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
        self.assertContains(response, customer.name)
        self.assertContains(response, product.name)
        self.assertContains(response, '₱17.00')
        self.assertNotContains(response, 'Private other')
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

    def test_authentication_templates_and_controls_are_retained(self):
        for route in ('/login/', '/register/'):
            response = self.client.get(route)
            self.assertContains(response, 'id="back-to-landing-btn"')
            self.assertContains(response, 'class="container-auth"')
