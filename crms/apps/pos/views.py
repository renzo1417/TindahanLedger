import json
from uuid import uuid4
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from apps.home.models import SalesTransaction
from apps.home.services import current_store, ordered_batches, checkout
from apps.home.templatetags.ledger_ui import artwork_for_unit
from django.templatetags.static import static


@login_required
def terminal_view(request):
    store = request.store = current_store(request.user)
    products = []
    for product in store.products.select_related('category').prefetch_related('batches').order_by('name'):
        products.append({'id': product.pk, 'name': product.name, 'sku': product.sku, 'unit': product.unit,
            'image': static('images/app/' + artwork_for_unit(product.unit) + '.svg'),
            'category': product.category.name if product.category else 'Uncategorized', 'price': str(product.selling_price),
            'stock': sum(b.quantity for b in ordered_batches(product))})
    return render(request, 'pos/pos_terminal.html', {'active_nav': 'pos', 'catalog': products,
        'customers': store.customers.order_by('name'), 'categories': sorted({p['category'] for p in products}), 'checkout_token': str(uuid4())})


@login_required
@require_POST
def checkout_view(request):
    store = current_store(request.user)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError
        sale = checkout(store, payload)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'The basket could not be read. Please retry.'}, status=400)
    except ValidationError as error:
        return JsonResponse({'error': ' '.join(error.messages)}, status=400)
    return JsonResponse({'receipt_no': sale.receipt_no, 'total': str(sale.total_amount),
        'change': str(sale.change_amount), 'receipt_url': reverse('pos:receipt', args=[sale.pk])})


@login_required
def receipt_view(request, sale_id):
    store = request.store = current_store(request.user)
    sale = get_object_or_404(SalesTransaction.objects.select_related('customer'), store=store, pk=sale_id)
    return render(request, 'pos/receipt.html', {'active_nav': 'pos', 'sale': sale, 'items': sale.items.select_related('product', 'batch')})
