from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from apps.home.forms import StoreProfileForm
from apps.home.services import current_store, lock_store


@login_required
def profile_view(request):
    store = request.store = current_store(request.user)
    form = StoreProfileForm(request.POST or None, instance=store, initial={'email': request.user.email})
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            lock_store(store)
            form.save()
            request.user.email = form.cleaned_data['email']
            names = store.owner_name.split(' ', 1)
            request.user.first_name = names[0]
            request.user.last_name = names[1] if len(names) > 1 else ''
            request.user.save(update_fields=['email', 'first_name', 'last_name'])
        messages.success(request, 'Store profile saved.')
        return redirect('profile:index')
    return render(request, 'profile/profile.html', {'active_nav': 'profile', 'form': form, 'store': store})
