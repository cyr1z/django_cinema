from datetime import datetime, timedelta

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.utils.datastructures import MultiValueDictKeyError
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
    queryset = Session.objects.filter(
        date_finish__gte=datetime.now().date(),
        date_start__lte=datetime.now().date(),
        )

    # Add date today and tomorrow to context
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        today = datetime.now().date()
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        date = today.strftime('%Y-%m-%d')
        context.update({'today': today, 'tomorrow': tomorrow, 'date': date})
        return context


class TomorrowSessionsView(ListView):
    """
    List of sessions
    """
    model = Session
    paginate_by = 6
    template_name = 'tomorrow-list-full.html'
    queryset = Session.objects.filter(
        date_finish__gte=(datetime.now() + timedelta(days=1)).date(),
        date_start__lte=(datetime.now() + timedelta(days=1)).date(),
        )

    # Add date today and tomorrow to context
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        today = datetime.now().date()
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        date = tomorrow.strftime('%Y-%m-%d')
        context.update({'today': today, 'tomorrow': tomorrow, 'date': date})
        return context


class SessionDetailView(LoginRequiredMixin, DetailView):
    """
    Session with ticket buying
    """
    model = Session
    template_name = 'movie-page-full.html'

    # Add date today and tomorrow to context
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        date = datetime.now().date()
        try:
            if str(self.request.GET['date']):
                q_date = str(self.request.GET['date'])
                date_t = datetime(*[int(item) for item in q_date.split('-')])
                date = date_t.date()
        except MultiValueDictKeyError:
            pass

        context.update({'date': date})
        return context


