from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, Form
from datetime import datetime as dt, timedelta

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
    #  TODO: VALIDATORS!!!
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


class MultiSeatsField(forms.MultipleChoiceField):
    def to_python(self, value):
        if not value:
            return []
        if all(i.isdigit() for i in value):
            return list(int(i) for i in value)
        else:
            raise forms.ValidationError('Invalid date')

    def clean(self, value):
        return list(set(value))


class BuyTicketForm(Form):
    session = forms.IntegerField(widget=forms.HiddenInput())
    date = forms.DateField(widget=forms.HiddenInput())
    seat_numbers = MultiSeatsField(label='')

    def clean_date(self):
        today = dt.now().date()
        tomorrow = today + timedelta(days=1)
        ticket_date = self.cleaned_data.get('date')
        if today <= ticket_date <= tomorrow:
            return ticket_date
        raise forms.ValidationError('Invalid date')

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        session_id = int(cleaned_data.get("session"))

        if all(i.isdigit() for i in cleaned_data.get("seat_numbers")):
            seat_numbers = (int(i) for i in cleaned_data.get("seat_numbers"))
            seat_numbers = set(seat_numbers)
        else:
            raise forms.ValidationError('Invalid seat numbers')

        session = Session.objects.get(id=session_id)
        bought_seats = session.session_tickets.filter(date=date)
        bought_seats_numbers = set(i.seat_number for i in bought_seats)
        all_seats = set(range(1, session.room.seats_count + 1))
        free_seats = all_seats - bought_seats_numbers

        if not set(seat_numbers).issubset(free_seats):
            raise forms.ValidationError('Invalid seats numbers')

        if session.date_start > date or \
                session.date_finish < date:
            raise forms.ValidationError('Invalid session')
