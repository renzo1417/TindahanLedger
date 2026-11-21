from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from apps.home.forms import ProductCreateForm, ProductEditForm, RestockForm, ExpiryForm
from apps.home.models import Category, Product, ProductBatch
from apps.home.selectors import batches_for
from apps.home.services import current_store, preferences, create_product, restock, dispose_batch, correct_expiry, lock_store


def inventory_presentation(store):
    products = list(store.products.select_related('category').order_by('name'))
    batches = batches_for(store)
    by_product = {}
    for batch in batches:
        if batch.quantity > 0 and not batch.disposed_at:
            by_product.setdefault(batch.product_id, []).append(batch)
    for product in products:
        active = by_product.get(product.pk, [])
        dated = [b for b in active if b.expiry_date]
        product.next_expiry = min(dated, key=lambda b: b.expiry_date) if dated else None
        product.expiry_flags = {b.display_status for b in active}
        if product.stock_quantity <= 0:
            product.display_status, product.display_label = 'out_of_stock', 'Out of stock'
        elif 'expired' in product.expiry_flags:
            product.display_status, product.display_label = 'expired', 'Expired batch'
        elif 'missing_date' in product.expiry_flags:
            product.display_status, product.display_label = 'missing_date', 'Expiry date needed'
        elif 'expiring_soon' in product.expiry_flags:
            product.display_status, product.display_label = 'expiring_soon', 'Expiring soon'
        elif product.stock_quantity <= product.low_stock_threshold:
            product.display_status, product.display_label = 'low_stock', 'Low stock'
        else:
            product.display_status, product.display_label = 'healthy', 'In stock'
    return products, batches


@login_required
def inventory_list_view(request):
    store = request.store = current_store(request.user)
    all_products, batches = inventory_presentation(store)
    products = all_products
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    if query:
        products = [p for p in products if query.casefold() in f'{p.name} {p.sku}'.casefold()]
    if category:
        products = [p for p in products if p.category and p.category.name == category]
    if status:
        products = [p for p in products if p.stock_status == status]
    selected_filter = request.GET.get('filter', 'all')
    if selected_filter == 'low_stock':
        products = [p for p in products if p.stock_quantity <= p.low_stock_threshold]
    elif selected_filter in ('expiring_soon', 'expired'):
        products = [p for p in products if selected_filter in p.expiry_flags]
    return render(request, 'inventory/inventory_list.html', {'active_nav': 'inventory', 'products': products,
        'categories': store.categories.order_by('name'), 'search_query': query, 'selected_category': category,
        'selected_status': status, 'product_count': len(all_products), 'total_units': sum(p.stock_quantity for p in all_products),
        'inventory_cost': sum(b.cost_price*b.quantity for b in batches if not b.disposed_at),
        'selected_filter': selected_filter,
        'attention_count': sum(b.quantity > 0 and not b.disposed_at and b.display_status in ('expired', 'expiring_soon', 'missing_date') for b in batches),
        'low_stock_count': sum(p.stock_quantity <= p.low_stock_threshold for p in all_products),
        'expiring_count': sum('expiring_soon' in p.expiry_flags for p in all_products),
        'expired_count': sum('expired' in p.expiry_flags for p in all_products)})


@login_required
def product_create_view(request):
    store = request.store = current_store(request.user)
    form = ProductCreateForm(request.POST or None, initial={'low_stock_threshold': preferences(store).low_stock_threshold})
    if request.method == 'POST' and form.is_valid():
        try:
            product = create_product(store, form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Product added to inventory.')
            return redirect('inventory:product_detail', product_id=product.pk)
    return render(request, 'inventory/product_create.html', {'active_nav': 'inventory', 'form': form})


def _detail(request, store, product, form=None, restock_form=None, status=200):
    form = form or ProductEditForm(instance=product, initial={'category_name': product.category.name if product.category else ''})
    restock_form = restock_form or RestockForm(prefix='restock', initial={'cost_price': product.cost_price, 'selling_price': product.selling_price})
    batches = [b for b in batches_for(store) if b.product_id == product.pk]
    dated = [b for b in batches if b.quantity > 0 and not b.disposed_at and b.expiry_date]
    return render(request, 'inventory/product_detail.html', {'active_nav': 'inventory', 'product': product,
        'form': form, 'restock_form': restock_form, 'batches': batches,
        'next_batch': min(dated, key=lambda b: b.expiry_date) if dated else None}, status=status)


@login_required
def product_detail_view(request, product_id):
    store = request.store = current_store(request.user)
    product = get_object_or_404(Product.objects.select_related('category'), store=store, pk=product_id)
    if request.method == 'POST':
        # Previous restock detail POST remains compatible.
        if 'quantity' in request.POST:
            return restock_view(request, product_id)
        form = ProductEditForm(request.POST, instance=product)
        if form.is_valid():
            with transaction.atomic():
                lock_store(store)
                product = get_object_or_404(Product, store=store, pk=product_id)
                category = form.cleaned_data['category_name'].strip()
                product.category = Category.objects.get_or_create(store=store, name=category)[0] if category else None
                for name, value in form.cleaned_data.items():
                    if name != 'category_name':
                        setattr(product, name, value)
                product.save()
            messages.success(request, 'Product details saved. Past sale costs are unchanged.')
            return redirect('inventory:product_detail', product_id=product.pk)
        return _detail(request, store, product, form=form, status=400)
    return _detail(request, store, product)


@login_required
@require_POST
def restock_view(request, product_id):
    store = request.store = current_store(request.user)
    product = get_object_or_404(Product, store=store, pk=product_id)
    form = RestockForm(request.POST, prefix='restock' if 'restock-quantity' in request.POST else None)
    if form.is_valid():
        try:
            restock(store, product_id, form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Stock batch saved.')
            return redirect('inventory:product_detail', product_id=product_id)
    return _detail(request, store, product, restock_form=form, status=400)


@login_required
@require_POST
def dispose_view(request, batch_id):
    store = current_store(request.user)
    batch = get_object_or_404(ProductBatch, product__store=store, pk=batch_id)
    if request.POST.get('confirm') != 'yes':
        messages.error(request, 'Confirm disposal before removing stock.')
    else:
        try:
            dispose_batch(store, batch_id)
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
        else:
            messages.success(request, 'Batch disposed. Stock and recorded loss updated.')
    return redirect('inventory:product_detail', product_id=batch.product_id)


@login_required
@require_POST
def expiry_update_view(request, batch_id):
    store = current_store(request.user)
    batch = get_object_or_404(ProductBatch, product__store=store, pk=batch_id)
    form = ExpiryForm(request.POST)
    if form.is_valid():
        try:
            correct_expiry(store, batch_id, form.cleaned_data['expiry_date'])
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
        else:
            messages.success(request, 'Batch expiry date corrected.')
    else:
        messages.error(request, 'Enter a valid expiry date.')
    return redirect('inventory:product_detail', product_id=batch.product_id)


@login_required
def expiry_tracker_view(request):
    store = request.store = current_store(request.user)
    batches = [b for b in batches_for(store) if b.quantity > 0 and not b.disposed_at]
    groups = [{'title': title, 'key': key, 'batches': [b for b in batches if b.display_status == key]}
              for key, title in [('expired', 'Expired · remove from shelves'), ('missing_date', 'Expiry date needed'),
                                 ('expiring_soon', 'Approaching expiry'), ('healthy', 'Healthy stock')]]
    selected = request.GET.get('filter', 'all')
    visible_groups = [g for g in groups if selected == 'all' or selected == 'attention' and g['key'] != 'healthy' or selected == 'missing_date' and g['key'] == 'missing_date']
    return render(request, 'inventory/expiry_tracker.html', {'active_nav': 'expiry', 'groups': visible_groups,
        'batch_count': len(batches), 'at_risk': sum(b.at_risk for b in batches), 'window': preferences(store).expiry_window_days,
        'selected_filter': selected, 'attention_count': sum(b.display_status != 'healthy' for b in batches),
        'missing_count': sum(b.display_status == 'missing_date' for b in batches)})
