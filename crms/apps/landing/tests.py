from django.test import TestCase, Client
from django.urls import reverse


class LandingPageSmokeTests(TestCase):
    """
    Acceptance smoke tests for the public landing page (/welcome/).
    Verifies route resolution, template rendering, brand copy,
    coherent arithmetic, account link presence, and zero database mutations.
    """

    def setUp(self):
        self.client = Client()

    def test_landing_route_resolves_and_renders_publicly(self):
        """Landing page at / and /welcome/ renders with HTTP 200 without login."""
        for route in ('/', '/welcome/'):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'landing/landing.html')

    def test_reverse_landing_url(self):
        """'landing:landing' reverses to / and 'landing:welcome' reverses to /welcome/."""
        self.assertEqual(reverse('landing:landing'), '/')
        self.assertEqual(reverse('landing:welcome'), '/welcome/')

    def test_auth_return_links_and_versioned_landing_assets(self):
        """Auth return links load the redesigned template with fresh asset URLs."""
        landing_url = reverse('landing:landing')
        for auth_url in (reverse('login:login'), reverse('register:register')):
            response = self.client.get(auth_url)
            self.assertContains(response, f'href="{landing_url}"')
            self.assertContains(response, 'id="back-to-landing-btn"')
        response = self.client.get(landing_url)
        self.assertContains(response, '/static/css/landing/landing.css?v=lively-1')
        self.assertContains(response, '/static/js/landing/landing.js?v=lively-1')

    def test_brand_copy_and_product_story(self):
        """The page explains the product in the redesigned Filipino voice."""
        response = self.client.get('/welcome/')
        content = response.content.decode('utf-8')

        # Hero copy
        self.assertIn("PARA SA ARAW-ARAW NA TINDAHAN", content)
        self.assertIn("Bawat galaw.", content)
        self.assertIn("Malinaw.", content)
        self.assertIn("Utang, bayad, at stock sa isang talaan", content)

        # Demo branding & sample labeling
        self.assertIn("Sample ledger · Demo only", content)
        self.assertIn("Aling Rosa", content)

        # Inventory story
        self.assertIn("dapat unahin.", content)
        self.assertIn("Mas maagang expiry, mas maagang ibenta.", content)
        self.assertIn("Pancit Canton", content)
        self.assertIn("BT-2026-081", content)
        self.assertIn("BT-2026-095", content)
        self.assertIn("Expired na", content)

        # Daily overview & coherent accounting
        self.assertIn("Kita ang galaw", content)
        self.assertIn("470.00", content)  # Sales recorded: ₱470.00
        self.assertIn("270.00", content)  # Payments received: ₱270.00

        # FAQ items
        self.assertIn("Para kanino ang TindaHan Ledger?", content)
        self.assertIn("Totoong customer data ba ang demo?", content)
        self.assertIn("Paano magsisimula?", content)

        # Closing CTA
        self.assertIn("Mas maayos ang", content)

    def test_static_demo_is_complete_without_javascript(self):
        response = self.client.get('/welcome/')
        self.assertContains(response, 'class="lp-stage-controls" hidden')
        self.assertContains(response, 'id="demo-balance">₱200.00')
        self.assertContains(response, '₱350.00 − ₱150.00 = ₱200.00')
        self.assertContains(response, 'Huwag ibenta')

    def test_anonymous_landing_does_not_query_or_mutate_records(self):
        """The public demonstrations render independently of store records."""
        with self.assertNumQueries(0):
            response = self.client.get('/welcome/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'alingnena.tindahan@gmail.com')
        self.assertNotContains(response, '+63 917 555 0192')

    def test_inventory_priority_and_expired_stock_are_coherent(self):
        """Expiry ordering differs from arrival order and excludes expired stock."""
        response = self.client.get('/welcome/')
        batches = response.context['inventory_batches']
        sellable = [batch for batch in batches if batch['is_sellable']]
        self.assertEqual([batch['days_remaining'] for batch in sellable], [3, 24, 60])
        self.assertEqual([batch['arrival_order'] for batch in sellable], [3, 2, 1])
        expired = [batch for batch in batches if not batch['is_sellable']]
        self.assertEqual(len(expired), 1)
        self.assertLess(expired[0]['days_remaining'], 0)
        self.assertContains(response, 'aria-label="Expired sample stock"')

    def test_demo_arithmetic_consistency(self):
        """Verifies coherent demo arithmetic: ₱350 debt - ₱150 payment = ₱200 balance."""
        response = self.client.get('/welcome/')
        content = response.content.decode('utf-8')

        self.assertIn("250.00", content)  # Rice purchase
        self.assertIn("100.00", content)  # Store items purchase
        self.assertIn("350.00", content)  # Total Utang
        self.assertIn("150.00", content)  # Bayad
        self.assertIn("200.00", content)  # Outstanding balance

    def test_account_and_anchor_links_present(self):
        """Resolves login and registration links correctly in rendered HTML."""
        response = self.client.get('/welcome/')
        content = response.content.decode('utf-8')

        login_url = reverse('login:login')
        register_url = reverse('register:register')

        self.assertIn(f'href="{login_url}"', content)
        self.assertIn(f'href="{register_url}"', content)
        self.assertIn('href="#ledger-demo"', content)
        self.assertIn('href="#inventory-story"', content)
        self.assertIn('href="#daily-overview"', content)
        self.assertIn('href="#faq"', content)

    def test_existing_dashboard_routes_unaffected(self):
        """Dashboard overview routes 'home:index' and 'home:home' resolve to '/home/' and remain functional."""
        self.assertEqual(reverse('home:index'), '/home/')
        self.assertEqual(reverse('home:home'), '/home/')

        resp_home = self.client.get('/home/')
        self.assertEqual(resp_home.status_code, 200)
        self.assertTemplateUsed(resp_home, 'home/home.html')
