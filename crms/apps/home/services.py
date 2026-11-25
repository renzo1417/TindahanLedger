"""Store-scoped writes. A store row lock serializes stock and balance changes."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.user_settings.models import UserSettings
from .models import (Category, Customer, CustomerLedgerTransaction, DailyStoreSummary,
                     Product, ProductBatch, SalesTransaction, SalesTransactionItem, Store)

ZERO = Decimal('0.00')


def money(value):
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result < 0 or result > Decimal('9999999999.99'):
            raise ValueError
        if result != result.quantize(Decimal('.01')):
            raise ValueError
        return result.quantize(Decimal('.01'))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError('Enter a valid, nonnegative amount with at most two decimal places.')


def current_store(user):
    return get_object_or_404(Store.objects.select_related('user__auth_user'), user__auth_user=user)


def preferences(store):
    # Migrations and account creation provision this row; GET requests never seed data.
    return UserSettings.objects.get(user_id=store.user.auth_user_id)


def lock_store(store):
    return Store.objects.select_for_update().get(pk=store.pk)


def sync_stock(product):
    batches = product.batches.filter(disposed_at__isnull=True, quantity__gt=0)
    product.stock_quantity = batches.aggregate(total=Sum('quantity'))['total'] or 0
    product.active_batches_count = batches.count()
    product.save()


def sellable_batches(product):
    batches = product.batches.filter(quantity__gt=0, disposed_at__isnull=True)
    batches = batches.exclude(expiry_date__lt=timezone.localdate())
    if product.has_expiry:
        batches = batches.filter(expiry_date__isnull=False)
    return batches.order_by('expiry_date', 'created_at', 'pk')


def ordered_batches(product):
    # Explicit ordering is identical on SQLite and PostgreSQL (NULL ordering differs).
    return sorted(sellable_batches(product), key=lambda b: (b.expiry_date or date.max, b.created_at, b.pk))


@transaction.atomic
def create_product(store, data):
    lock_store(store)
    data = dict(data)
    category_name = data.pop('category_name', '').strip()
    quantity = data.pop('stock_quantity', 0)
    batch_code = data.pop('batch_code', '')
    expiry = data.pop('expiry_date', None)
    location = data.pop('shelf_location', '')
    category = None
    if category_name:
        category, _ = Category.objects.get_or_create(store=store, name=category_name)
    product = Product.objects.create(store=store, category=category, **data)
    if quantity:
        _add_batch(product, quantity, product.cost_price, product.selling_price, batch_code, expiry, location)
    return product


def _add_batch(product, quantity, cost, selling, code='', expiry=None, location=''):
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        raise ValidationError('Restock quantity must be a positive whole number.')
    if product.has_expiry and not expiry:
        raise ValidationError('An expiry date is required for this product.')
    if expiry and expiry < timezone.localdate():
        raise ValidationError('New stock cannot already be expired.')
    cost, selling = money(cost), money(selling)
    ProductBatch.objects.create(product=product, quantity=quantity, cost_price=cost,
                                selling_price=selling, batch_code=code or f'BT-{uuid4().hex[:12].upper()}',
                                expiry_date=expiry, shelf_location=location)
    product.cost_price, product.selling_price = cost, selling
    sync_stock(product)


@transaction.atomic
def restock(store, product_id, data):
    lock_store(store)
    product = get_object_or_404(Product, pk=product_id, store=store)
    _add_batch(product, data['quantity'], data['cost_price'], data['selling_price'],
               data.get('batch_code', ''), data.get('expiry_date'), data.get('shelf_location', ''))
    return product


@transaction.atomic
def dispose_batch(store, batch_id):
    lock_store(store)
    batch = get_object_or_404(ProductBatch.objects.select_related('product'), pk=batch_id, product__store=store)
    if batch.disposed_at or batch.quantity <= 0:
        raise ValidationError('This batch has no remaining stock to dispose of.')
    batch.disposed_quantity = batch.quantity
    batch.capital_loss = batch.cost_price * batch.quantity
    batch.quantity = 0
    batch.disposed_at = timezone.now()
    batch.save()
    sync_stock(batch.product)
    return batch


@transaction.atomic
def correct_expiry(store, batch_id, expiry):
    lock_store(store)
    batch = get_object_or_404(ProductBatch.objects.select_related('product'), pk=batch_id, product__store=store)
    if batch.disposed_at or batch.quantity <= 0:
        raise ValidationError('Only a batch with remaining stock can be corrected.')
    batch.expiry_date = expiry
    batch.save()


def _ledger_entry(store, customer, kind, amount, summary='', due_date=None, payment_mode='Cash', sale=None, notes=''):
    amount = money(amount)
    if amount <= 0:
        raise ValidationError('The amount must be greater than zero.')
    if kind == 'bayad':
        if amount > customer.running_balance:
            raise ValidationError('Payment cannot exceed the outstanding balance.')
        customer.running_balance -= amount
        customer.last_payment_date = timezone.localdate()
    elif kind == 'utang':
        if preferences(store).block_over_limit and customer.running_balance + amount > customer.credit_limit:
            raise ValidationError('This entry would exceed the customer’s credit limit.')
        customer.running_balance += amount
        if due_date and (not customer.due_date or due_date < customer.due_date or customer.running_balance == amount):
            customer.due_date = due_date
    else:
        raise ValidationError('Choose a valid ledger action.')
    if customer.running_balance == 0:
        customer.due_date = None
    customer.save()
    return CustomerLedgerTransaction.objects.create(
        customer=customer, sales_transaction=sale, reference_no=f'TL-{uuid4().hex[:16].upper()}',
        transaction_type=kind, type_label='Payment' if kind == 'bayad' else ('POS credit sale' if sale else 'Debt adjustment'),
        amount=amount, running_balance=customer.running_balance,
        payment_mode=payment_mode if kind == 'bayad' else '', items_summary=summary,
        due_date=due_date, notes=notes)


def sync_daily_summary(store, report_date=None):
    """Upsert the DailyStoreSummary snapshot for a store on the given Philippine calendar day."""
    day = report_date or timezone.localdate()
    start = timezone.make_aware(datetime.combine(day, time.min))
    end = timezone.make_aware(datetime.combine(day + timedelta(days=1), time.min))
    sales = SalesTransaction.objects.filter(
        store=store, transaction_type='sale', transaction_date__gte=start, transaction_date__lt=end
    )
    figures = sales.aggregate(
        gross_sales=Sum('total_amount'),
        gross_margin=Sum('profit_earned'),
        transactions_count=Count('pk'),
    )
    gross_sales = figures['gross_sales'] or ZERO
    gross_margin = figures['gross_margin'] or ZERO
    transactions_count = figures['transactions_count'] or 0
    cash_sales = sales.filter(payment_method='Cash').aggregate(total=Sum('total_amount'))['total'] or ZERO
    payments_received = (
        CustomerLedgerTransaction.objects.filter(
            customer__store=store, transaction_type='bayad', transaction_date__gte=start, transaction_date__lt=end
        ).aggregate(total=Sum('amount'))['total']
        or ZERO
    )
    uncollected_utang = Customer.objects.filter(store=store).aggregate(total=Sum('running_balance'))['total'] or ZERO
    if gross_sales > ZERO:
        raw_pct = (gross_margin / gross_sales * Decimal('100')).quantize(Decimal('.01'))
        margin_pct = max(Decimal('-999.99'), min(Decimal('999.99'), raw_pct))
    else:
        margin_pct = ZERO
    summary, _ = DailyStoreSummary.objects.update_or_create(
        store=store,
        report_date=day,
        defaults={
            'gross_sales': gross_sales,
            'gross_margin': gross_margin,
            'margin_pct': margin_pct,
            'cash_collected': cash_sales + payments_received,
            'uncollected_utang': uncollected_utang,
            'transactions_count': transactions_count,
        },
    )
    return summary


@transaction.atomic
def record_entry(store, customer_id, **data):
    lock_store(store)
    customer = get_object_or_404(Customer, store=store, pk=customer_id)
    entry = _ledger_entry(store, customer, **data)
    sync_daily_summary(store)
    return entry


@transaction.atomic
def create_customer(store, data):
    lock_store(store)
    data = dict(data)
    balance = data.pop('initial_balance', ZERO)
    summary = data.pop('initial_summary', '')
    customer = Customer.objects.create(store=store, **data)
    if balance:
        _ledger_entry(store, customer, 'utang', balance, summary or 'Opening balance')
    return customer


@transaction.atomic
def checkout(store, payload):
    lock_store(store)
    try:
        token = UUID(str(payload.get('token', '')))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError('Invalid checkout token. Reload the terminal.')
    existing = SalesTransaction.objects.filter(store=store, checkout_token=token).first()
    if existing:
        return existing
    method = payload.get('payment_method')
    if method not in ('Cash', 'Utang'):
        raise ValidationError('Choose Cash or Utang.')
    items = payload.get('items')
    if not isinstance(items, list) or not items or len(items) > 200:
        raise ValidationError('Add between 1 and 200 products to the basket.')
    quantities = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError('Invalid basket item.')
        product_id, quantity = item.get('product_id'), item.get('quantity')
        if type(product_id) is not int or type(quantity) is not int or quantity <= 0 or quantity > 100000:
            raise ValidationError('Each product needs a positive whole-number quantity.')
        quantities[product_id] = quantities.get(product_id, 0) + quantity
    products = list(Product.objects.filter(store=store, pk__in=quantities).order_by('pk'))
    if len(products) != len(quantities):
        raise ValidationError('One or more products are unavailable.')
    customer, due = None, None
    if method == 'Utang':
        try:
            customer_id = int(payload.get('customer_id', ''))
            due = date.fromisoformat(str(payload.get('due_date', '')))
        except (ValueError, TypeError):
            raise ValidationError('Select a customer and a valid due date.')
        if due < timezone.localdate():
            raise ValidationError('The due date cannot be in the past.')
        customer = Customer.objects.filter(pk=customer_id, store=store).first()
        if customer is None:
            raise ValidationError('Selected customer was not found in your store.')
    allocations = []
    total, profit = ZERO, ZERO
    for product in products:
        remaining = quantities[product.pk]
        if product.selling_price <= 0:
            raise ValidationError(f'{product.name} needs a selling price before checkout.')
        for batch in ordered_batches(product):
            taken = min(remaining, batch.quantity)
            allocations.append((product, batch, taken))
            total += product.selling_price * taken
            profit += (product.selling_price - batch.cost_price) * taken
            remaining -= taken
            if not remaining:
                break
        if remaining:
            raise ValidationError(f'Not enough sellable stock for {product.name}. Review its batches.')
    total, profit = money(total), profit.quantize(Decimal('.01'))
    tendered = money(payload.get('cash_tendered', 0)) if method == 'Cash' else ZERO
    if method == 'Cash' and tendered < total:
        raise ValidationError('Cash received is less than the sale total.')
    summary = ', '.join(f'{quantities[p.pk]} × {p.name}' for p in products)
    sale = SalesTransaction.objects.create(store=store, customer=customer, checkout_token=token,
        receipt_no=f'TL-{uuid4().hex[:16].upper()}', payment_method=method,
        items_count=sum(quantities.values()), items_summary=summary, subtotal_amount=total,
        total_amount=total, cash_tendered=tendered, change_amount=tendered-total if method == 'Cash' else ZERO,
        profit_earned=profit)
    if customer:
        _ledger_entry(store, customer, 'utang', total, summary, due, sale=sale)
    for product, batch, quantity in allocations:
        SalesTransactionItem.objects.create(transaction=sale, product=product, batch=batch, quantity=quantity,
                                            unit_price=product.selling_price, cost_price=batch.cost_price)
        batch.quantity -= quantity
        batch.save()
    for product in products:
        sync_stock(product)
    sync_daily_summary(store)
    return sale
