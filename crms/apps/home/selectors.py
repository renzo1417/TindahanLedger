"""Read-only presentation data shared by dashboards, reports, and navigation."""
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Sum, Count, F
from django.utils import timezone

from .models import Customer, Product, ProductBatch, SalesTransaction, SalesTransactionItem, CustomerLedgerTransaction
from .services import ZERO, preferences


def customer_status(customer, grace_days=7):
    customer.available_credit = max(ZERO, customer.credit_limit - customer.running_balance)
    customer.days_overdue = max(0, (timezone.localdate()-customer.due_date).days) if customer.due_date and customer.running_balance > 0 else 0
    customer.status = 'settled' if customer.running_balance <= 0 else ('overdue' if customer.days_overdue > grace_days else 'active')
    customer.status_label = {'settled': 'Settled', 'active': 'Active', 'overdue': f'{customer.days_overdue} days past due'}[customer.status]
    return customer


def customers_for(store):
    grace = preferences(store).overdue_grace_days
    return [customer_status(c, grace) for c in Customer.objects.filter(store=store).order_by('-running_balance', 'name')]


def batch_status(batch, window=7):
    batch.remaining_cost = batch.cost_price * batch.quantity
    batch.days_left = (batch.expiry_date-timezone.localdate()).days if batch.expiry_date else None
    if batch.disposed_at:
        batch.display_status, batch.display_label = 'disposed', 'Disposed'
    elif batch.quantity <= 0:
        batch.display_status, batch.display_label = 'depleted', 'Sold out'
    elif batch.days_left is None:
        batch.display_status = 'missing_date' if batch.product.has_expiry else 'healthy'
        batch.display_label = 'Expiry date needed' if batch.product.has_expiry else 'No expiry tracking'
    elif batch.days_left < 0:
        batch.display_status, batch.display_label = 'expired', f'Expired {abs(batch.days_left)} days ago'
    elif batch.days_left <= window:
        batch.display_status, batch.display_label = 'expiring_soon', f'Expires in {batch.days_left} days'
    else:
        batch.display_status, batch.display_label = 'healthy', 'Healthy'
    batch.at_risk = batch.cost_price * batch.quantity if batch.display_status in ('expired', 'expiring_soon', 'missing_date') else ZERO
    return batch


def batches_for(store):
    window = preferences(store).expiry_window_days
    return [batch_status(b, window) for b in ProductBatch.objects.filter(product__store=store).select_related('product').order_by('expiry_date', 'created_at')]


def period_start(timeframe):
    today = timezone.localdate()
    day = today.replace(day=1) if timeframe == 'this_month' else today
    return timezone.make_aware(datetime.combine(day, time.min)) if timeframe != 'all_time' else None


def financial_report(store, timeframe='today'):
    start = period_start(timeframe)
    sales = SalesTransaction.objects.filter(store=store, transaction_type='sale')
    payments = CustomerLedgerTransaction.objects.filter(customer__store=store, transaction_type='bayad')
    if start:
        sales = sales.filter(transaction_date__gte=start)
        payments = payments.filter(transaction_date__gte=start)
    today = timezone.localdate()
    end_day = (today.replace(day=28)+timedelta(days=4)).replace(day=1) if timeframe == 'this_month' else today+timedelta(days=1)
    end = timezone.make_aware(datetime.combine(end_day, time.min))
    sales = sales.filter(transaction_date__lt=end)
    payments = payments.filter(transaction_date__lt=end)
    figures = sales.aggregate(gross_sales=Sum('total_amount'), gross_profit=Sum('profit_earned'), transactions_count=Count('pk'))
    revenue, profit = figures['gross_sales'] or ZERO, figures['gross_profit'] or ZERO
    cash_sales = sales.filter(payment_method='Cash').aggregate(total=Sum('total_amount'))['total'] or ZERO
    collections = payments.aggregate(total=Sum('amount'))['total'] or ZERO
    outstanding = Customer.objects.filter(store=store).aggregate(total=Sum('running_balance'))['total'] or ZERO
    summary = dict(gross_sales=revenue, gross_profit=profit, cost_of_goods=revenue-profit,
                   cash_sales=cash_sales, utang_sales=revenue-cash_sales,
                   cash_share=(cash_sales/revenue*100).quantize(Decimal('.1')) if revenue else ZERO,
                   utang_share=((revenue-cash_sales)/revenue*100).quantize(Decimal('.1')) if revenue else ZERO,
                   margin_pct=(profit/revenue*100).quantize(Decimal('.1')) if revenue else ZERO,
                   cash_collected=cash_sales+collections, payments_received=collections,
                   uncollected_utang=outstanding, transactions_count=figures['transactions_count'])
    top = SalesTransactionItem.objects.filter(transaction__in=sales).values('product_id', 'product__name', 'product__unit').annotate(
        units_sold=Sum('quantity'), revenue=Sum('subtotal_amount'), profit=Sum('profit_amount')).order_by('-units_sold', 'product__name')[:10]
    return summary, list(top)


def store_kpis(store):
    customers = customers_for(store)
    batches = batches_for(store)
    summary, _ = financial_report(store)
    products = Product.objects.filter(store=store)
    return {
        'today_sales_total': summary['gross_sales'], 'today_sales_count': summary['transactions_count'],
        'total_utang_balance': summary['uncollected_utang'],
        'overdue_accounts_count': sum(c.status == 'overdue' for c in customers),
        'active_utang_accounts_count': sum(c.running_balance > 0 for c in customers),
        'settled_accounts_count': sum(c.running_balance <= 0 for c in customers),
        'low_stock_items_count': products.filter(stock_quantity__lte=F('low_stock_threshold')).count(),
        'expiry_alert_batches_count': sum(b.quantity > 0 and b.display_status in ('expired', 'expiring_soon', 'missing_date') for b in batches),
        'expired_batches_count': sum(b.display_status == 'expired' for b in batches),
    }


def sms_message(customer, store, tone='polite'):
    greeting = f'Magandang araw po, {customer.name}.'
    balance = f'₱{customer.running_balance:,.2f}'
    message = f'{greeting} Paalala mula sa {store.store_name}: ang inyong utang ay {balance}.'
    if tone == 'firm':
        message += ' Paki-settle po ang inyong balanse sa lalong madaling panahon.'
    else:
        message += ' Maaari po kayong magbayad sa tindahan.'
    if store.gcash_number:
        message += f' Maaari ring mag-GCash sa {store.gcash_number}.'
    return message + ' Salamat po!'
