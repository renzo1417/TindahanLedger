from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.home.models import Customer, SMSReminder
from apps.home.selectors import customers_for, sms_message
from apps.home.services import current_store, preferences, lock_store


@login_required
def reminders_view(request):
    store = request.store = current_store(request.user)
    tone = 'firm' if request.GET.get('tone') == 'firm' else 'polite'
    threshold = timezone.localdate()+timedelta(days=preferences(store).reminder_threshold_days)
    customers = [c for c in customers_for(store) if c.running_balance > 0]
    for customer in customers:
        customer.sms_preview = sms_message(customer, store, tone)
        customer.reminder_due = bool(customer.due_date and customer.due_date <= threshold)
    selected = next((c for c in customers if str(c.pk) == request.GET.get('customer')), customers[0] if customers else None)
    return render(request, 'reminders/sms_reminders.html', {'active_nav': 'reminders', 'customers': customers,
        'tone': tone, 'selected_customer': selected, 'history': store.sms_reminders.filter(sent_status='simulated').select_related('customer').order_by('-created_at')[:20]})


@login_required
@require_POST
def simulate_view(request, customer_id):
    store = current_store(request.user)
    tone = 'firm' if request.POST.get('tone') == 'firm' else 'polite'
    with transaction.atomic():
        lock_store(store)
        customer = get_object_or_404(Customer, pk=customer_id, store=store)
        if customer.running_balance <= 0 or not customer.phone.strip():
            messages.error(request, 'A positive balance and customer phone number are required for this demo.')
        else:
            SMSReminder.objects.create(store=store, customer=customer, tone=tone, phone_number=customer.phone,
                message_content=sms_message(customer, store, tone), balance_at_send=customer.running_balance,
                sent_status='simulated', sent_at=None)
            messages.success(request, 'Simulation recorded. No SMS was sent and no charges were made.')
    return redirect('reminders:sms_reminders')
