"""
Landing page view for TindaHan Ledger.
Vertical slice: apps.landing.views
Serves the public landing page at / (and /welcome/) with render-only sample data.
Zero database mutations or external API dependencies.
"""

from datetime import date, timedelta
from django.shortcuts import render


def landing_view(request):
    """
    Renders the public landing page with coherent relative-date sample data
    for the inventory expiry-priority story and daily transaction tape.
    """
    today = date.today()

    # Formatted relative dates for inventory batches
    batch_urgent_date = today + timedelta(days=3)
    batch_fresh_date = today + timedelta(days=24)
    batch_safe_date = today + timedelta(days=60)
    batch_expired_date = today - timedelta(days=5)

    inventory_batches = [
        {
            'product_name': "Lucky Me Pancit Canton (Calamansi)",
            'batch_code': "BT-2026-081",
            'shelf_location': "Estante A-1 • Harap (Front)",
            'quantity': 12,
            'unit': "packs",
            'expiry_date': batch_urgent_date.strftime("%b %d, %Y"),
            'days_remaining': 3,
            'arrival_order': 3,
            'status': "urgent_sell",
            'status_label': "Unahing Ibenta (3 araw na lang)",
            'is_highlighted': True,
            'is_sellable': True,
            'notes': "Pinakamaagang mag-expire — ibenta bago buksan ang bagong kahon.",
        },
        {
            'product_name': "Lucky Me Pancit Canton (Calamansi)",
            'batch_code': "BT-2026-095",
            'shelf_location': "Estante A-1 • Likod (Back)",
            'quantity': 36,
            'unit': "packs",
            'expiry_date': batch_fresh_date.strftime("%b %d, %Y"),
            'days_remaining': 24,
            'arrival_order': 2,
            'status': "fresh",
            'status_label': "Fresh Stock (24 araw pa)",
            'is_highlighted': False,
            'is_sellable': True,
            'notes': "Itabi sa likod hanggang maubos ang mas lumang batch.",
        },
        {
            'product_name': "Mega Sardines in Tomato Sauce (Red)",
            'batch_code': "BT-2026-072",
            'shelf_location': "Estante B-2",
            'quantity': 18,
            'unit': "cans",
            'expiry_date': batch_safe_date.strftime("%b %d, %Y"),
            'days_remaining': 60,
            'arrival_order': 1,
            'status': "safe",
            'status_label': "Ligtas (60 araw pa)",
            'is_highlighted': False,
            'is_sellable': True,
            'notes': "Normal na rotation sa istante.",
        },
        {
            'product_name': "Bear Brand Fortified Powdered Milk (33g)",
            'batch_code': "BT-2026-031",
            'shelf_location': "Nakahukay / Kahon ng Segregasyon",
            'quantity': 4,
            'unit': "pouches",
            'expiry_date': batch_expired_date.strftime("%b %d, %Y"),
            'days_remaining': -5,
            'status': "expired",
            'status_label': "Expired na (5 araw nakalipas)",
            'is_highlighted': False,
            'is_sellable': False,
            'notes': "Huwag ibenta! Tanggalin sa istante at i-record bilang loss.",
        },
    ]

    # Daily overview transactions (strictly coherent accounting)
    # Cash sale ₱120.00 + Utang credit sale ₱350.00 = Total sales recorded ₱470.00
    # Cash sale ₱120.00 + Bayad settlement ₱150.00 = Total payments received ₱270.00
    daily_transactions = [
        {
            'time': "07:15 AM",
            'customer_name': "Walk-in Suki",
            'transaction_type': "Cash Sale",
            'type_badge_class': "badge-settled",
            'items_summary': "1x Mantika (lapad), 2x Itlog",
            'receipt_no': "CSH-1041",
            'amount': 120.00,
            'accounting_effect': "Benta at Cash: +₱120.00",
        },
        {
            'time': "08:30 AM",
            'customer_name': "Aling Rosa",
            'transaction_type': "Pautang (Credit)",
            'type_badge_class': "badge-active-outline",
            'items_summary': "Bigas (₱250.00), Tindahan items (₱100.00)",
            'receipt_no': "CRD-1042",
            'amount': 350.00,
            'accounting_effect': "Benta: +₱350.00 (Utang balance)",
        },
        {
            'time': "04:45 PM",
            'customer_name': "Aling Rosa",
            'transaction_type': "Bayad Settlement",
            'type_badge_class': "badge-success",
            'items_summary': "Bahagyang bayad sa pautang",
            'receipt_no': "PAY-1043",
            'amount': 150.00,
            'accounting_effect': "Cash: +₱150.00 (Bawas sa Utang)",
        },
    ]

    daily_summary = {
        'sales_recorded': 470.00,
        'payments_received': 270.00,
        'cash_sales': 120.00,
        'utang_sales': 350.00,
        'bayad_collected': 150.00,
    }

    context = {
        'today_display': today.strftime("%B %d, %Y"),
        'inventory_batches': inventory_batches,
        'daily_transactions': daily_transactions,
        'daily_summary': daily_summary,
    }

    return render(request, 'landing/landing.html', context)
