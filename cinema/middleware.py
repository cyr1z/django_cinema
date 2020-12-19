from django.contrib.auth import logout
from datetime import datetime as dt

from django_cinema.settings import SESSION_IDLE_TIMEOUT, DATATIME_FORMAT

from django.utils.deprecation import MiddlewareMixin


class AutoLogout(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated or request.user.is_staff:
            return
        now = dt.now()
        last_action_not_decoded = request.session.get('last_action')
        if last_action_not_decoded:
            last_action = dt.strptime(last_action_not_decoded, DATATIME_FORMAT)
            if (now - last_action).seconds > SESSION_IDLE_TIMEOUT:
                logout(request)
        request.session['last_action'] = now.strftime(DATATIME_FORMAT)
