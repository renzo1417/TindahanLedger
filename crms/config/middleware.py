import logging

from django.db import DatabaseError
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template

logger = logging.getLogger(__name__)


class DatabaseErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, DatabaseError):
            return None
        # Do not log connection strings or database exception text containing credentials.
        logger.error('Database request failed: %s', type(exception).__name__)
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'The database is unavailable. Please retry.'}, status=503)
        # Rendering without RequestContext prevents a second database query from
        # authentication/store context processors while the database is down.
        return HttpResponse(get_template('database_unavailable.html').render({}), status=503)
