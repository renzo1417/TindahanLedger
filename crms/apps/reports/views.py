from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.home.selectors import financial_report
from apps.home.services import current_store


@login_required
def financial_reports_view(request):
    store = request.store = current_store(request.user)
    timeframe = request.GET.get('timeframe', 'today')
    if timeframe not in ('today', 'this_month', 'all_time'):
        timeframe = 'today'
    summary, products = financial_report(store, timeframe)
    return render(request, 'reports/financial_reports.html', {'active_nav': 'reports',
        'selected_timeframe': timeframe, 'summary': summary, 'top_products': products})
