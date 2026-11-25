from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
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
    return render(
        request,
        'profile/profile.html',
        {
            'active_nav': 'profile',
            'form': form,
            'store': store,
            'password_form': PasswordChangeForm(request.user),
        },
    )


@login_required
@require_POST
def password_change_view(request):
    store = request.store = current_store(request.user)
    password_form = PasswordChangeForm(request.user, request.POST)
    if password_form.is_valid():
        user = password_form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password updated.')
        return redirect('profile:index')
    return render(
        request,
        'profile/profile.html',
        {
            'active_nav': 'profile',
            'form': StoreProfileForm(instance=store, initial={'email': request.user.email}),
            'store': store,
            'password_form': password_form,
        },
        status=400,
    )
