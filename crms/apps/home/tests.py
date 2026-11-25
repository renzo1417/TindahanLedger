import json
from datetime import datetime, time, timedelta
from decimal import Decimal
from io import StringIO
from unittest import mock, skipUnless
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from .forms import ProductCreateForm
from .models import (User, Customer, CustomerLedgerTransaction, DailyStoreSummary, Product, ProductBatch,
                     SalesTransaction, SalesTransactionItem, Store, SMSReminder)
from .selectors import financial_report, batch_status, customer_status
from .services import (checkout, create_customer, create_product, current_store, dispose_batch,
                       preferences, record_entry, restock, correct_expiry)


class LedgerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.account = get_user_model().objects.create_user(username='merchant', password='Store#password2026')
        cls.other_account = get_user_model().objects.create_user(username='another-merchant', password='Store#password2026')
        cls.store = current_store(cls.account)
        cls.other_store = current_store(cls.other_account)

    def setUp(self):
        self.client.force_login(self.account)

    def product(self, store=None, **changes):
        data = dict(name='Coffee <special>', category_name='Drinks', sku='COF-01', unit='sachet',
                    selling_price=Decimal('15.00'), cost_price=Decimal('10.00'), low_stock_threshold=3,
                    stock_quantity=20, has_expiry=True, expiry_date=timezone.localdate()+timedelta(days=5))
        data.update(changes)
        return create_product(store or self.store, data)

    def customer(self, store=None, **changes):
        data = dict(name='Customer', phone='09000000000', credit_limit=Decimal('3000.00'))
        data.update(changes)
        return create_customer(store or self.store, data)

    def payload(self, product, **changes):
        data = {'token': str(uuid4()), 'payment_method': 'Cash', 'cash_tendered': '100',
                'items': [{'product_id': product.pk, 'quantity': 3}]}
        data.update(changes)
        return data

    def test_all_business_routes_require_login(self):
        self.client.logout()
        for route in ('/home/', '/utang/', '/inventory/', '/inventory/register/', '/expiry/', '/pos/', '/reports/', '/reminders/', '/profile/', '/settings/', '/search/', '/settings/export/ledger.json'):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 302)

    def test_page_loads_do_not_seed_records(self):
        before = {model: model.objects.count() for model in (User, Store, Customer, Product, ProductBatch, SalesTransaction, SMSReminder)}
        for route in ('/home/', '/utang/', '/inventory/', '/inventory/register/', '/expiry/', '/pos/', '/reports/', '/reminders/', '/profile/', '/settings/', '/utang/entry/'):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 200)
        self.assertEqual(before, {model: model.objects.count() for model in before})

    def test_store_ownership_uses_explicit_link(self):
        self.assertEqual(self.store.user.auth_user_id, self.account.pk)
        self.assertNotEqual(self.store.pk, self.other_store.pk)

    def test_cash_checkout_batch_cost_and_deduplication(self):
        product = self.product()
        payload = self.payload(product)
        sale = checkout(self.store, payload)
        self.assertEqual(sale.total_amount, Decimal('45.00'))
        self.assertEqual(sale.change_amount, Decimal('55.00'))
        self.assertEqual(sale.profit_earned, Decimal('15.00'))
        product.refresh_from_db()
        self.assertEqual(product.stock_quantity, 17)
        self.assertEqual(checkout(self.store, payload).pk, sale.pk)
        self.assertEqual(SalesTransaction.objects.count(), 1)
        product.refresh_from_db()
        self.assertEqual(product.stock_quantity, 17)
        self.assertEqual(sale.items.get().cost_price, Decimal('10.00'))

    def test_utang_checkout_updates_ledger_and_reports_once(self):
        product, customer = self.product(), self.customer()
        sale = checkout(self.store, self.payload(product, payment_method='Utang', customer_id=customer.pk,
                            due_date=(timezone.localdate()+timedelta(days=7)).isoformat()))
        customer.refresh_from_db()
        self.assertEqual(customer.running_balance, Decimal('45'))
        self.assertEqual(customer.ledger_transactions.get().sales_transaction_id, sale.pk)
        summary, _ = financial_report(self.store)
        self.assertEqual(summary['gross_sales'], Decimal('45'))
        self.assertEqual(summary['cash_collected'], Decimal('0'))
        record_entry(self.store, customer.pk, kind='bayad', amount='20', payment_mode='Cash')
        summary, _ = financial_report(self.store)
        self.assertEqual(summary['cash_collected'], Decimal('20'))
        self.assertEqual(summary['uncollected_utang'], Decimal('25'))
        self.assertEqual(summary['gross_sales'], Decimal('45'))

    def test_manual_debt_does_not_create_sales_or_change_stock(self):
        product, customer = self.product(), self.customer()
        record_entry(self.store, customer.pk, kind='utang', amount='50')
        customer.refresh_from_db(); product.refresh_from_db()
        self.assertEqual(customer.running_balance, Decimal('50'))
        self.assertEqual(product.stock_quantity, 20)
        self.assertFalse(SalesTransaction.objects.exists())

    def test_credit_failure_rolls_back_whole_sale(self):
        product, customer = self.product(), self.customer(credit_limit=Decimal('10'))
        with self.assertRaises(ValidationError):
            checkout(self.store, self.payload(product, payment_method='Utang', customer_id=customer.pk,
                     due_date=(timezone.localdate()+timedelta(days=1)).isoformat()))
        product.refresh_from_db(); customer.refresh_from_db()
        self.assertEqual(product.stock_quantity, 20)
        self.assertEqual(customer.running_balance, 0)
        self.assertFalse(SalesTransaction.objects.exists())
        self.assertFalse(CustomerLedgerTransaction.objects.exists())

    def test_insufficient_cash_and_stock_leave_no_partial_writes(self):
        product = self.product()
        for payload in [self.payload(product, cash_tendered='1'), self.payload(product, items=[{'product_id': product.pk, 'quantity': 21}])]:
            with self.assertRaises(ValidationError):
                checkout(self.store, payload)
        product.refresh_from_db()
        self.assertEqual(product.stock_quantity, 20)
        self.assertFalse(SalesTransaction.objects.exists())

    def test_multi_product_failure_rolls_back_earlier_allocations(self):
        product, empty = self.product(), self.product(name='Empty', stock_quantity=0)
        with self.assertRaises(ValidationError):
            checkout(self.store, self.payload(product, items=[{'product_id': product.pk, 'quantity': 1}, {'product_id': empty.pk, 'quantity': 1}]))
        product.refresh_from_db()
        self.assertEqual(product.stock_quantity, 20)
        self.assertFalse(SalesTransactionItem.objects.exists())

    def test_earliest_expiry_is_allocated_first_and_split_costs_are_saved(self):
        product = self.product(expiry_date=timezone.localdate()+timedelta(days=20), stock_quantity=5)
        restock(self.store, product.pk, {'quantity': 2, 'cost_price': '12', 'selling_price': '15', 'expiry_date': timezone.localdate()+timedelta(days=2)})
        sale = checkout(self.store, self.payload(product))
        lines = list(sale.items.order_by('pk'))
        self.assertEqual([line.quantity for line in lines], [2, 1])
        self.assertEqual([line.cost_price for line in lines], [Decimal('12'), Decimal('10')])
        self.assertEqual(sale.profit_earned, Decimal('11'))
        restock(self.store, product.pk, {'quantity': 1, 'cost_price': '14', 'selling_price': '20', 'expiry_date': timezone.localdate()+timedelta(days=30)})
        sale.refresh_from_db()
        self.assertEqual(sale.profit_earned, Decimal('11'))

    def test_expired_missing_date_and_disposed_batches_are_unsellable(self):
        for kind in ('expired', 'missing', 'disposed'):
            product = self.product(name=kind)
            batch = product.batches.get()
            if kind == 'expired':
                batch.expiry_date = timezone.localdate()-timedelta(days=1); batch.save()
            elif kind == 'missing':
                batch.expiry_date = None; batch.save()
            else:
                dispose_batch(self.store, batch.pk)
            with self.assertRaises(ValidationError):
                checkout(self.store, self.payload(product))

    def test_nondated_nonperishable_stock_can_be_sold(self):
        product = self.product(has_expiry=False, expiry_date=None)
        self.assertEqual(checkout(self.store, self.payload(product)).total_amount, Decimal('45'))

    def test_disposal_reduces_stock_and_records_loss_once(self):
        product = self.product()
        batch = dispose_batch(self.store, product.batches.get().pk)
        self.assertEqual(batch.disposed_quantity, 20)
        self.assertEqual(batch.capital_loss, Decimal('200'))
        product.refresh_from_db()
        self.assertEqual(product.stock_quantity, 0)
        with self.assertRaises(ValidationError):
            dispose_batch(self.store, batch.pk)
        self.assertFalse(SalesTransaction.objects.exists())

    def test_overpayment_is_rejected_and_exact_payment_settles(self):
        customer = self.customer(initial_balance=Decimal('50'))
        with self.assertRaises(ValidationError):
            record_entry(self.store, customer.pk, kind='bayad', amount='51')
        self.assertEqual(customer.ledger_transactions.count(), 1)
        record_entry(self.store, customer.pk, kind='bayad', amount='50')
        customer.refresh_from_db()
        self.assertEqual(customer.running_balance, 0)
        self.assertIsNone(customer.due_date)

    def test_settings_can_disable_credit_limit_enforcement(self):
        customer = self.customer(credit_limit=Decimal('1'))
        settings = preferences(self.store)
        settings.block_over_limit = False; settings.save()
        record_entry(self.store, customer.pk, kind='utang', amount='50')
        customer.refresh_from_db()
        self.assertEqual(customer.running_balance, Decimal('50'))

    def test_invalid_amounts_and_quantities_are_rejected(self):
        customer, product = self.customer(), self.product()
        for value in ('NaN', 'Infinity', '-1', '0', '1.001'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                record_entry(self.store, customer.pk, kind='utang', amount=value)
        for value in (True, -1, 0, 1.5, '3'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                checkout(self.store, self.payload(product, items=[{'product_id': product.pk, 'quantity': value}]))

    def test_other_store_details_writes_search_and_exports_are_scoped(self):
        product = self.product(self.other_store, name='Private other product')
        customer = self.customer(self.other_store, name='Private other customer')
        batch = product.batches.get()
        requests = [('get', f'/inventory/{product.pk}/', {}), ('get', f'/utang/{customer.pk}/', {}),
                    ('post', f'/inventory/{product.pk}/restock/', {}), ('post', f'/inventory/batches/{batch.pk}/dispose/', {'confirm': 'yes'}),
                    ('post', f'/reminders/{customer.pk}/simulate/', {}),
                    ('post', '/utang/entries/', {'customer_id': customer.pk, 'kind': 'utang', 'amount': '10'})]
        for method, route, data in requests:
            with self.subTest(route=route):
                self.assertEqual(getattr(self.client, method)(route, data).status_code, 404)
        self.assertEqual(self.client.get('/search/?q=Private').json()['results'], [])
        export = self.client.get('/settings/export/ledger.json')
        self.assertNotContains(export, 'Private other')
        self.assertNotContains(export, 'password')
        response = self.client.post('/pos/checkout/', data=json.dumps(self.payload(product)), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_product_form_and_restock_persist_after_refresh(self):
        response = self.client.post('/inventory/register/', {'name': 'Rice', 'category_name': 'Staples', 'unit': 'kg', 'cost_price': '40', 'selling_price': '50', 'low_stock_threshold': '3', 'stock_quantity': '10'})
        self.assertEqual(response.status_code, 302)
        product = self.store.products.get(name='Rice')
        self.assertEqual(self.client.get(f'/inventory/{product.pk}/').status_code, 200)
        response = self.client.post(f'/inventory/{product.pk}/restock/', {'quantity': '4', 'cost_price': '41', 'selling_price': '51'})
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.stock_quantity, 14)
        self.assertEqual(product.batches.count(), 2)

    def test_profile_and_settings_persist(self):
        response = self.client.post('/profile/', {'store_name': 'My actual store', 'owner_name': 'Owner Actual', 'email': 'owner@example.test', 'operating_hours': '7 AM to 8 PM'})
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get('/home/'), 'My actual store')
        response = self.client.post('/settings/', {'default_credit_limit': '4500', 'overdue_grace_days': '4', 'reminder_threshold_days': '2', 'expiry_window_days': '14', 'low_stock_threshold': '6', 'block_over_limit': 'on'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(preferences(self.store).default_credit_limit, Decimal('4500'))
        self.client.logout(); self.client.force_login(self.account)
        self.assertContains(self.client.get('/settings/'), '4500')

    def test_form_errors_preserve_input_without_fake_success(self):
        response = self.client.post('/inventory/register/', {'name': 'Keep this name', 'unit': 'pc', 'cost_price': '-1', 'selling_price': '20', 'low_stock_threshold': '3', 'stock_quantity': '2', 'has_expiry': 'on'})
        self.assertContains(response, 'Keep this name')
        self.assertContains(response, 'Enter the expiry date')
        self.assertFalse(Product.objects.exists())

    def test_simulated_sms_has_no_delivery_timestamp(self):
        customer = self.customer(initial_balance=Decimal('100'))
        response = self.client.post(f'/reminders/{customer.pk}/simulate/', {'tone': 'polite'})
        self.assertEqual(response.status_code, 302)
        reminder = SMSReminder.objects.get()
        self.assertEqual(reminder.sent_status, 'simulated')
        self.assertIsNone(reminder.sent_at)
        self.assertEqual(reminder.balance_at_send, Decimal('100'))
        self.assertContains(self.client.get('/reminders/'), 'No SMS is delivered')

    def test_report_uses_philippine_calendar_day(self):
        product = self.product()
        sale = checkout(self.store, self.payload(product))
        local_midnight = timezone.make_aware(datetime.combine(timezone.localdate(), time.min))
        SalesTransaction.objects.filter(pk=sale.pk).update(transaction_date=local_midnight-timedelta(seconds=1))
        self.assertEqual(financial_report(self.store)[0]['gross_sales'], Decimal('0'))
        SalesTransaction.objects.filter(pk=sale.pk).update(transaction_date=local_midnight+timedelta(seconds=1))
        self.assertEqual(financial_report(self.store)[0]['gross_sales'], Decimal('45'))

    def test_status_changes_without_saving_records(self):
        product = self.product()
        batch = product.batches.get()
        with mock.patch('apps.home.selectors.timezone.localdate', return_value=batch.expiry_date+timedelta(days=1)):
            self.assertEqual(batch_status(batch).display_status, 'expired')
        customer = self.customer(initial_balance=Decimal('50'), due_date=timezone.localdate()-timedelta(days=8))
        self.assertEqual(customer_status(customer, 7).status, 'overdue')
        self.assertEqual(customer_status(customer, 9).status, 'active')

    def test_csv_neutralizes_formula_cells(self):
        self.customer(name='=HYPERLINK("example")')
        response = self.client.get('/settings/export/customers.csv')
        self.assertIn("'=HYPERLINK", response.content.decode('utf-8'))

    def test_demo_command_is_explicit_isolated_and_idempotent(self):
        with mock.patch.dict('os.environ', {'DEMO_PASSWORD': 'School#demoPassword2026'}):
            call_command('seed_demo', username='classroom-demo', stdout=StringIO())
            counts = (Customer.objects.count(), Product.objects.count(), SalesTransaction.objects.count())
            call_command('seed_demo', username='classroom-demo', stdout=StringIO())
        self.assertEqual(counts, (Customer.objects.count(), Product.objects.count(), SalesTransaction.objects.count()))
        self.assertEqual(self.store.products.count(), 0)
        self.assertEqual(self.store.customers.count(), 0)

    def test_malformed_checkout_and_csrf_are_rejected(self):
        self.assertEqual(self.client.post('/pos/checkout/', data='[]', content_type='application/json').status_code, 400)
        from django.test import Client
        strict = Client(enforce_csrf_checks=True); strict.force_login(self.account)
        self.assertEqual(strict.post('/pos/checkout/', data='{}', content_type='application/json').status_code, 403)

    def test_external_login_redirect_is_ignored(self):
        self.client.logout()
        response = self.client.post('/login/?next=https://example.org/', {'identifier': 'merchant', 'password': 'Store#password2026'})
        self.assertRedirects(response, '/home/', fetch_redirect_response=False)

    def test_database_failure_renders_without_querying_context_again(self):
        from django.db import OperationalError
        with mock.patch('apps.home.views.current_store', side_effect=OperationalError('unavailable')):
            response = self.client.get('/home/')
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, 'couldn’t reach your ledger', status_code=503)

    def test_expiry_correction_restores_sellable_stock(self):
        product = self.product()
        batch = product.batches.get()
        ProductBatch.objects.filter(pk=batch.pk).update(expiry_date=None)
        correct_expiry(self.store, batch.pk, timezone.localdate()+timedelta(days=5))
        self.assertEqual(checkout(self.store, self.payload(product)).total_amount, Decimal('45'))

    def test_legacy_assignment_requires_apply_and_preserves_empty_store(self):
        owner = User.objects.create(username='unlinked-legacy', password_hash='unusable')
        legacy = Store.objects.create(user=owner, store_name='Legacy store', owner_name='Legacy merchant')
        Product.objects.create(store=legacy, name='Legacy product')
        count = Store.objects.count()
        call_command('assign_legacy_store', store=legacy.pk, username=self.account.username, stdout=StringIO())
        self.assertEqual(current_store(self.account).pk, self.store.pk)
        call_command('assign_legacy_store', store=legacy.pk, username=self.account.username, apply=True, stdout=StringIO())
        self.assertEqual(current_store(self.account).pk, legacy.pk)
        self.assertEqual(Store.objects.count(), count)
        self.store.refresh_from_db()
        self.assertEqual(self.store.user_id, owner.pk)

    def test_registration_saves_store_using_explicit_account_link(self):
        self.client.logout()
        User.objects.create(pk=100, username='preserve-unclaimed', password_hash='unusable')
        response = self.client.post('/register/', {'store_name': 'Actual new store', 'owner_name': 'New Merchant',
            'phone': '09123456789', 'password': 'School#LedgerExample2026', 'confirm_password': 'School#LedgerExample2026'})
        self.assertRedirects(response, '/login/', fetch_redirect_response=False)
        account = get_user_model().objects.get(username='09123456789')
        store = current_store(account)
        self.assertEqual(store.store_name, 'Actual new store')
        self.assertEqual(store.phone_number, '09123456789')
        self.assertNotEqual(store.user_id, account.pk)
        self.assertEqual(store.products.count(), 0)
        self.assertEqual(store.customers.count(), 0)

    def test_receipt_is_private_to_its_store(self):
        product = self.product(self.other_store)
        sale = checkout(self.other_store, self.payload(product))
        self.assertEqual(self.client.get(f'/pos/receipts/{sale.pk}/').status_code, 404)

    def test_logout_requires_post(self):
        self.assertEqual(self.client.get('/login/logout/').status_code, 405)
        self.assertEqual(self.client.get('/home/').status_code, 200)
        response = self.client.post('/login/logout/')
        self.assertRedirects(response, '/login/', fetch_redirect_response=False)
        self.assertEqual(self.client.get('/home/').status_code, 302)

    def test_login_with_case_insensitive_email(self):
        self.account.email = 'Owner@Store.PH'
        self.account.save(update_fields=['email'])
        self.client.logout()
        response = self.client.post('/login/', {'identifier': 'owner@store.ph', 'password': 'Store#password2026'})
        self.assertRedirects(response, '/home/', fetch_redirect_response=False)

    def test_pos_checkout_invalid_or_other_store_customer_returns_json_400(self):
        product = self.product()
        other_customer = self.customer(self.other_store, name='Other store customer')
        due = (timezone.localdate() + timedelta(days=3)).isoformat()
        for bad_customer_id in (999999, other_customer.pk):
            with self.subTest(customer_id=bad_customer_id):
                response = self.client.post(
                    '/pos/checkout/',
                    data=json.dumps(self.payload(product, payment_method='Utang', customer_id=bad_customer_id, due_date=due)),
                    content_type='application/json',
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.json())

    def test_customer_edit_updates_details_and_is_store_scoped(self):
        customer = self.customer(name='Aling Rosa', initial_balance=Decimal('120.00'))
        other_customer = self.customer(self.other_store, name='Private other customer')
        response = self.client.post(
            f'/utang/{customer.pk}/edit/',
            {
                'name': 'Mama Rosa',
                'nickname': 'Tindahan regular',
                'phone': '09171234567',
                'gcash': '09171234567',
                'address': 'Blk 2 Lot 5',
                'credit_limit': '5000.00',
                'notes': 'Updated note',
            },
        )
        self.assertRedirects(response, f'/utang/{customer.pk}/', fetch_redirect_response=False)
        customer.refresh_from_db()
        self.assertEqual(customer.name, 'Mama Rosa')
        self.assertEqual(customer.avatar_letter, 'M')
        self.assertEqual(customer.phone, '09171234567')
        self.assertEqual(customer.gcash, '09171234567')
        self.assertEqual(customer.credit_limit, Decimal('5000.00'))
        self.assertEqual(customer.running_balance, Decimal('120.00'))
        self.assertEqual(
            self.client.post(f'/utang/{other_customer.pk}/edit/', {'name': 'Hack', 'credit_limit': '100'}).status_code,
            404,
        )

    def test_password_change_updates_password_and_keeps_session(self):
        user_model = get_user_model()
        account = user_model.objects.create_user(username='pw-merchant', password='Old#Password2026')
        self.client.force_login(account)
        bad = self.client.post(
            '/profile/password/',
            {'old_password': 'Wrong#Password2026', 'new_password1': 'New#Password2026', 'new_password2': 'New#Password2026'},
        )
        self.assertEqual(bad.status_code, 400)
        self.assertContains(bad, 'data-auto-open', status_code=400)
        good = self.client.post(
            '/profile/password/',
            {'old_password': 'Old#Password2026', 'new_password1': 'New#Password2026', 'new_password2': 'New#Password2026'},
        )
        self.assertRedirects(good, '/profile/', fetch_redirect_response=False)
        self.assertEqual(self.client.get('/home/').status_code, 200)
        account.refresh_from_db()
        self.assertEqual(User.objects.get(auth_user=account).password_hash, account.password)
        self.client.post('/login/logout/')
        login_res = self.client.post('/login/', {'identifier': 'pw-merchant', 'password': 'New#Password2026'})
        self.assertRedirects(login_res, '/home/', fetch_redirect_response=False)

    def test_daily_store_summary_updates_on_checkout_and_payment(self):
        product = self.product()
        customer = self.customer(initial_balance=Decimal('100.00'))
        checkout(
            self.store,
            {'token': str(uuid4()), 'payment_method': 'Cash', 'cash_tendered': '50', 'items': [{'product_id': product.pk, 'quantity': 2}]},
        )
        summary = DailyStoreSummary.objects.get(store=self.store, report_date=timezone.localdate())
        self.assertEqual(summary.gross_sales, Decimal('30.00'))
        self.assertEqual(summary.gross_margin, Decimal('10.00'))
        self.assertEqual(summary.cash_collected, Decimal('30.00'))
        self.assertEqual(summary.uncollected_utang, Decimal('100.00'))
        self.assertEqual(summary.transactions_count, 1)
        record_entry(self.store, customer.pk, kind='bayad', amount='40.00', payment_mode='Cash')
        summary.refresh_from_db()
        self.assertEqual(summary.cash_collected, Decimal('70.00'))
        self.assertEqual(summary.uncollected_utang, Decimal('60.00'))
        self.assertEqual(summary.transactions_count, 1)


@skipUnless(connection.vendor == 'postgresql', 'Row-lock concurrency requires isolated PostgreSQL.')
class PostgreSQLConcurrencyTests(TransactionTestCase):
    def test_last_unit_cannot_be_sold_twice(self):
        from concurrent.futures import ThreadPoolExecutor
        from django.db import close_old_connections
        account = get_user_model().objects.create_user(username='concurrent-store')
        store = current_store(account)
        product = create_product(store, dict(name='Last unit', unit='pc', selling_price=Decimal('20'), cost_price=Decimal('10'),
                                 low_stock_threshold=1, has_expiry=False, stock_quantity=1))
        def attempt():
            close_old_connections()
            try:
                checkout(Store.objects.get(pk=store.pk), {'token': str(uuid4()), 'payment_method': 'Cash', 'cash_tendered': '20',
                    'items': [{'product_id': product.pk, 'quantity': 1}]})
                return True
            except ValidationError:
                return False
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: attempt(), range(2)))
        self.assertEqual(results.count(True), 1)
        product.refresh_from_db()
        self.assertEqual(product.stock_quantity, 0)
        self.assertEqual(SalesTransaction.objects.count(), 1)
