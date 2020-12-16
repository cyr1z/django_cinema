from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Form
from django.views.generic.edit import FormMixin
from datetime import datetime, timedelta

from cinema.models import CinemaUser, Room, Movie, Session


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
        fields = ['title', 'seats_count']


class MovieCreateForm(ModelForm):
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


class BuyTicketForm(Form):
    session = forms.IntegerField(widget=forms.HiddenInput())
    date = forms.DateField(widget=forms.HiddenInput())
    seat_numbers = forms.MultipleChoiceField(label='')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['seat_numbers'].choices = []

    class Meta:
        fields = [
            'session',
            'date',
            'seat_numbers',
        ]

    def clean_date(self):
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        data = self.cleaned_data['date']
        if today <= data <= tomorrow:
            return data
        raise ValidationError('Invalid date')


