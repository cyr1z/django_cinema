from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from cinema.models import CinemaUser, Ticket, Room, Movie, Session


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, required=False,
        help_text='Optional.')
    last_name = forms.CharField(
        max_length=30, required=False,
        help_text='Optional.')
    email = forms.EmailField(
        max_length=254,
        help_text='Required. Inform a valid email address.')

    phone = forms.CharField(
        max_length=30, required=False,
        help_text='Optional.')

    class Meta:
        model = CinemaUser
        fields = ('username', 'first_name', 'last_name',
                  'email', 'phone', 'password1', 'password2',)


class RoomCreateForm(ModelForm):
    class Meta:
        model = Room
        fields = ['title', 'seats_count',]


class MovieCreateForm(ModelForm):
    # image = forms.ImageField(required=False, help_text='Optional.')

    class Meta:
        model = Movie
        fields = [
            'title',
            'description',
            'duration',
            'director',
            'year',
            'poster',
        ]


class SessionCreateForm(ModelForm):
    # image = forms.ImageField(required=False, help_text='Optional.')

    class Meta:
        model = Session
        fields = [
            'movie',
            'room',
            'time_start',
            'time_finish',
            'date_start',
            'date_finish',
            'price',
        ]
