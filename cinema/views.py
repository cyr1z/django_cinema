from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.views.generic import CreateView, ListView, TemplateView, DetailView

from cinema.forms import SignUpForm
from cinema.models import Movie, Room


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
