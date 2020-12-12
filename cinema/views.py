import re
from datetime import datetime, timedelta

from django.db.models import Count, Q
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.views.generic import CreateView, ListView, TemplateView, DetailView

from cinema.forms import SignUpForm
from cinema.models import Movie, Room, Session


# Create your views here.
class UserLogin(LoginView):
    """ login """
    template_name = 'login.html'


class Register(CreateView):
    """ Sign UP """
    form_class = SignUpForm
    success_url = "/login/"
    template_name = "register.html"


class UserLogout(LoginRequiredMixin, LogoutView):
    """ Logout """
    next_page = '/'
    redirect_field_name = 'next'


class SessionsView(ListView):
    """
    List of sessions
    """
    model = Session
    paginate_by = 10
    template_name = 'movie-list-full.html'
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    queryset = Session.objects.filter(
        date_finish__gte=datetime.now().date(),
        date_start__lte=datetime.now().date(),
    ).annotate(
        tickets=Count('session_tickets',
                      filter=Q(session_tickets__date=today)))

    # Add date today and tomorrow to context
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        date = self.today.strftime('%Y-%m-%d')
        context.update({
            'today': self.today,
            'tomorrow': self.tomorrow,
            'date': date})
        return context


class TomorrowSessionsView(ListView):
    """
    List of sessions
    """
    model = Session
    paginate_by = 6
    template_name = 'tomorrow-list-full.html'
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    queryset = Session.objects.filter(
        date_finish__gte=(datetime.now() + timedelta(days=1)).date(),
        date_start__lte=(datetime.now() + timedelta(days=1)).date(),
    ).annotate(
        tickets=Count('session_tickets',
                      filter=Q(session_tickets__date=tomorrow)))

    # Add date today and tomorrow to context
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        date = self.tomorrow.strftime('%Y-%m-%d')
        context.update({
            'today': self.today,
            'tomorrow': self.tomorrow,
            'date': date,
        })
        return context


class SessionDetailView(DetailView):
    """
    Session with ticket buying
    """
    model = Session
    template_name = 'movie-page-full.html'

    def get_date(self):
        """ Get date from request for select today/tomorrow """
        regexp_date = "^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$"
        q_date = str(self.request.GET.get('date', ''))
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        if q_date and re.match(regexp_date, q_date):
            date = datetime(*[int(item) for item in q_date.split('-')]).date()
            if today <= date <= tomorrow and date <= self.object.date_finish:
                return date
        return today

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        # Add date today or tomorrow to context
        date = self.get_date()

        bought_seats = self.object.session_tickets.filter(date=date)
        bought_seats_numbers = set(i.seat_number for i in bought_seats)
        all_seats = set(range(1, self.object.room.seats_count + 1))
        free_seats = list(all_seats - bought_seats_numbers)
        free_seats_count = len(free_seats)
        session_tickets_count = len(bought_seats_numbers)
        context.update({
            'date': date,
            'free_seats': free_seats,
            'free_seats_count': free_seats_count,
            'session_tickets_count': session_tickets_count,
        })
        return context
