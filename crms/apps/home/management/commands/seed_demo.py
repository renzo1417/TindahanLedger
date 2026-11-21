"""Explicit, transactional classroom setup. Never invoked by a web request."""
from datetime import timedelta
from decimal import Decimal
from getpass import getpass
from uuid import uuid4
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.home.models import Store
from apps.home.services import create_customer, create_product, checkout, record_entry, current_store


class Command(BaseCommand):
    help = 'Create an isolated classroom demo account. Set DEMO_PASSWORD or enter a password at the prompt.'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Dedicated demo sign-in username.')

    @transaction.atomic
    def handle(self, *args, **options):
        username = options['username']
        User = get_user_model()
        existing = User.objects.filter(username=username).first()
        if existing:
            store = Store.objects.filter(user__auth_user=existing).first()
            if store and store.is_demo:
                self.stdout.write('Demo already exists. No records were changed.')
                return
            raise CommandError('That account already exists and is not a demo. Choose a dedicated username.')
        password = os.environ.get('DEMO_PASSWORD') or getpass('Demo account password: ')
        try:
            validate_password(password, User(username=username))
        except ValidationError as error:
            raise CommandError(' '.join(error.messages))
        user = User.objects.create_user(username=username, password=password, first_name='Classroom', last_name='Merchant')
        store = current_store(user)
        store.store_name, store.owner_name, store.is_demo = 'Classroom Tindahan', 'Demo Merchant', True
        store.address, store.ledger_volume = 'Classroom demonstration', 'Demo ledger'
        store.save()
        today = timezone.localdate()
        definitions = [('Pancit Canton', 'Noodles', 'pack', '10.00', '15.00', 30, 3),
                       ('Sardines', 'Canned goods', 'can', '19.00', '25.00', 20, 30),
                       ('Bottled water', 'Drinks', 'bottle', '8.00', '12.00', 24, None),
                       ('Coffee sachet', 'Drinks', 'sachet', '6.00', '10.00', 40, 60),
                       ('Laundry soap', 'Household', 'bar', '14.00', '20.00', 12, None),
                       ('Crackers', 'Snacks', 'pack', '7.00', '10.00', 18, 12)]
        products = []
        for index, (name, category, unit, cost, price, quantity, days) in enumerate(definitions, 1):
            products.append(create_product(store, dict(name=name, category_name=category, unit=unit,
                sku=f'DEMO-{index:03}', cost_price=Decimal(cost), selling_price=Decimal(price),
                low_stock_threshold=10, has_expiry=days is not None, stock_quantity=quantity,
                expiry_date=today+timedelta(days=days) if days else None)))
        customer = create_customer(store, dict(name='Demo Customer', nickname='Aling Demo', phone='09000000000',
            credit_limit=Decimal('3000'), initial_balance=Decimal('200'), initial_summary='Demo opening balance',
            due_date=today-timedelta(days=12)))
        create_customer(store, dict(name='Second Demo Customer', nickname='Mang Demo', phone='09000000001', credit_limit=Decimal('3000')))
        checkout(store, {'token': str(uuid4()), 'payment_method': 'Cash', 'cash_tendered': '100',
            'items': [{'product_id': products[0].pk, 'quantity': 2}, {'product_id': products[2].pk, 'quantity': 2}]})
        checkout(store, {'token': str(uuid4()), 'payment_method': 'Utang', 'customer_id': customer.pk,
            'due_date': (today+timedelta(days=7)).isoformat(), 'items': [{'product_id': products[1].pk, 'quantity': 2}]})
        record_entry(store, customer.pk, kind='bayad', amount=Decimal('50'), payment_mode='Cash', summary='Demo partial payment')
        # Include expired stock for the expiry workflow without admitting it as new stock.
        batch = products[3].batches.get()
        batch.expiry_date = today-timedelta(days=2)
        batch.save()
        self.stdout.write(self.style.SUCCESS('Classroom demo created. Sign in with the supplied username and password.'))
