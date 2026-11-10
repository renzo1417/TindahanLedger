"""
Reports and Financial Analytics view for TindaHan Ledger.
Vertical slice: apps.reports
Serves the store financial reports, cash reconciliation, utang aging, and inventory risk overview.
"""

from datetime import date
from django.shortcuts import render


def reports_view(request):
    """Renders the Store Financial & Credit Reports screen."""
    today = date.today()
    current_date_display = today.strftime("%B %d, %Y")

    # Financial KPIs
    financial_kpis = {
        'today_sales_total': 5420.00,
        'today_cash_collected': 4180.00,
        'total_utang_receivables': 12450.00,
        'overdue_utang_total': 3820.00,
        'sales_transactions_count': 34,
        'utang_settlements_count': 8,
    }

    # Daily Cash & Sales Reconciliation
    cash_reconciliation = {
        'cash_sales': 2930.00,
        'credit_sales': 2490.00,
        'utang_collections': 1250.00,
        'cash_in_drawer': 4180.00,
        'cash_sales_pct': 54.1,
        'credit_sales_pct': 45.9,
    }

    # Revenue by Category
    category_breakdown = [
        {'name': 'Rice & Grains (Bigas)', 'amount': 1950.00, 'percentage': 36},
        {'name': 'Canned Goods & Instant Meals', 'amount': 1380.00, 'percentage': 25},
        {'name': 'Beverages & 3-in-1 Coffee', 'amount': 1140.00, 'percentage': 21},
        {'name': 'Household & Toiletry Sachets', 'amount': 950.00, 'percentage': 18},
    ]

    # Aging of Accounts Receivable (Utang Aging)
    aging_accounts = [
        {
            'customer_name': 'Nanay Linda',
            'phone': '0917-882-3401',
            'balance': 1150.00,
            'days_overdue': 28,
            'last_payment_date': 'Oct 13, 2026',
            'last_payment_amount': 200.00,
            'status': 'critical',
            'status_label': '28 araw na',
        },
        {
            'customer_name': 'Kuya Jun',
            'phone': '0928-554-1922',
            'balance': 1430.00,
            'days_overdue': 22,
            'last_payment_date': 'Oct 19, 2026',
            'last_payment_amount': 150.00,
            'status': 'overdue',
            'status_label': '22 araw na',
        },
        {
            'customer_name': 'Ate Marites',
            'phone': '0905-331-8840',
            'balance': 1240.00,
            'days_overdue': 17,
            'last_payment_date': 'Oct 24, 2026',
            'last_payment_amount': 300.00,
            'status': 'overdue',
            'status_label': '17 araw na',
        },
        {
            'customer_name': 'Mang Celso',
            'phone': '0919-447-2109',
            'balance': 850.00,
            'days_overdue': 8,
            'last_payment_date': 'Nov 02, 2026',
            'last_payment_amount': 250.00,
            'status': 'normal',
            'status_label': '8 araw na',
        },
        {
            'customer_name': 'Aling Rosa',
            'phone': '0918-123-4567',
            'balance': 200.00,
            'days_overdue': 3,
            'last_payment_date': 'Nov 07, 2026',
            'last_payment_amount': 150.00,
            'status': 'settled',
            'status_label': '3 araw na',
        },
    ]

    # Inventory Expiry Risk (FIFO Prioritization)
    expiry_risk_items = [
        {
            'product_name': 'Lucky Me Pancit Canton (Calamansi)',
            'batch_code': 'BT-2026-081',
            'shelf_location': 'Estante A-1 • Harap',
            'quantity': 12,
            'unit': 'packs',
            'days_remaining': 3,
            'estimated_value': 180.00,
            'action_label': 'Unahing Ibenta',
        },
        {
            'product_name': 'Argentina Corned Beef 150g',
            'batch_code': 'BT-2026-041',
            'shelf_location': 'Estante B-2 • Harap',
            'quantity': 8,
            'unit': 'cans',
            'days_remaining': 5,
            'estimated_value': 360.00,
            'action_label': 'Unahing Ibenta',
        },
        {
            'product_name': 'Nestea Iced Tea Sachet',
            'batch_code': 'BT-2026-038',
            'shelf_location': 'Estante C-1 • Gitna',
            'quantity': 24,
            'unit': 'sachets',
            'days_remaining': 6,
            'estimated_value': 288.00,
            'action_label': 'I-display sa Harap',
        },
        {
            'product_name': 'Bear Brand Fortified 33g',
            'batch_code': 'BT-2026-064',
            'shelf_location': 'Estante A-3 • Harap',
            'quantity': 16,
            'unit': 'sachets',
            'days_remaining': 7,
            'estimated_value': 416.00,
            'action_label': 'I-display sa Harap',
        },
    ]

    total_risk_value = sum(item['estimated_value'] for item in expiry_risk_items)

    context = {
        'active_nav': 'reports',
        'current_date': current_date_display,
        'kpis': financial_kpis,
        'reconciliation': cash_reconciliation,
        'categories': category_breakdown,
        'aging_accounts': aging_accounts,
        'expiry_risk_items': expiry_risk_items,
        'total_risk_value': total_risk_value,
    }

    return render(request, 'reports/reports.html', context)
