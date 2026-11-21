from django.utils import timezone
from apps.home.models import Store
from apps.home.selectors import store_kpis


def global_store_context(request):
    if not request.user.is_authenticated or request.path in ('/', '/welcome/', '/login/', '/register/'):
        return {}
    store = getattr(request, 'store', None)
    if store is None:
        store = Store.objects.filter(user__auth_user=request.user).select_related('user__auth_user').first()
    if store is None:
        return {}
    return {'global_store_profile': {
        'store_name': store.store_name, 'owner_name': store.owner_name, 'address': store.address,
        'gcash_number': store.gcash_number, 'avatar_initial': store.store_name[:1].upper(),
        'current_date_display': timezone.localtime().strftime('%d %b %Y')},
        'global_store_kpis': store_kpis(store)}
