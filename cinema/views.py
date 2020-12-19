import re
from datetime import datetime as dt, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from cinema.forms import SignUpForm, RoomCreateForm, MovieCreateForm, \
    SessionCreateForm, BuyTicketForm
from cinema.models import Movie, Room, Session, Ticket

from django_cinema.settings import DATE_REGEXP


class UserLogin(LoginView):
    """ login """
    template_name = 'login.html'
    success_url = "/"


class Register(CreateView):
    """ Sign UP """
    form_class = SignUpForm
    success_url = "/login/"
    template_name = "register.html"


@method_decorator(staff_member_required, name='dispatch')
class UserLogout(LogoutView):
    """ Logout """
    next_page = "/"
    success_url = "/"
    redirect_field_name = 'next'


class SessionsView(ListView):
    """
    List of sessions
    """
    model = Session
    paginate_by = 10
    template_name = 'movie-list-full.html'
    today = dt.now().date()
    now_time = dt.now().time()
    tomorrow = today + timedelta(days=1)
    queryset = Session.objects.filter(
        date_finish__gte=today,
        date_start__lte=today,
    ).filter(
        time_start__gte=now_time
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
    today = dt.now().date()
    tomorrow = today + timedelta(days=1)
    queryset = Session.objects.filter(
        date_finish__gte=tomorrow,
        date_start__lte=tomorrow,
    ).annotate(
        tickets=Count(
            'session_tickets',
            filter=Q(session_tickets__date=tomorrow))
    )

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
        regexp_date = DATE_REGEXP
        text_date = str(self.request.GET.get('date', ''))
        today = dt.now().date()
        tomorrow = today + timedelta(days=1)
        if text_date and re.match(regexp_date, text_date):
            date = dt.strptime(text_date, '%Y-%m-%d').date()
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
        form = BuyTicketForm(self.request.POST or None)
        form.fields['date'].initial = date
        form.fields['session'].initial = self.object.id
        free_seats_choices = [(str(x), x) for x in free_seats]
        form.fields['seat_numbers'].choices = free_seats_choices
        form.fields['seat_numbers'].widget.attrs.update(
            {'class': 'form-control', 'size': '10'})
        context.update({
            'form': form,
            'date': date,
            'free_seats': free_seats,
            'free_seats_count': free_seats_count,
            'session_tickets_count': session_tickets_count,
        })
        return context


@method_decorator(login_required, name='dispatch')
class TicketsBuyView(CreateView):
    """
        Create tickets
    """
    form_class = BuyTicketForm
    success_url = '/tickets/'

    # sepcify name of template
    # template_name = "edit.html"

    def post(self, *args, **kwargs):
        # save form data to object, not to database

        form = BuyTicketForm(self.request.POST)
        print(form.is_valid())
        data = dict(form.data)
        session = Session.objects.get(id=int(data['session'][0]))
        seat_numbers = data['seat_numbers']
        text_date = data['date'][0]
        date = dt.strptime(text_date, '%Y-%m-%d').date()
        user = self.request.user
        object = {
            'date': date,
            'session': session,
            'user': user,
        }

        objects = []
        for seat in seat_numbers:
            object = {
                'date': date,
                'session': session,
                'user': user,
                'seat_number': int(seat)
            }
            objects.append(object)

        Ticket.objects.bulk_create([Ticket(**q) for q in objects])

        return HttpResponseRedirect(self.success_url)


@method_decorator(login_required, name='dispatch')
class TicketsListView(ListView):
    """
    List of sessions
    """
    model = Ticket
    paginate_by = 15
    template_name = 'tickets-list.html'
    today = dt.now().date()

    # add user filter to queryset
    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        old_tickets = self.object_list.filter(date__lt=self.today)
        new_tickets = self.object_list.filter(date__gte=self.today)
        tickets_count = self.object_list.aggregate(Count('id'))
        money_sum = self.object_list.aggregate(Sum('session__price'))

        context.update({
            'old_tickets': old_tickets,
            'new_tickets': new_tickets,
            'tickets_count': tickets_count['id__count'],
            'money_sum': money_sum['session__price__sum'],
        })
        return context


@method_decorator(staff_member_required, name='dispatch')
class RoomCreateView(CreateView):
    """
    Create Room. Only for administrators.
    """
    model = Room
    template_name = 'edit.html'
    form_class = RoomCreateForm
    success_url = '/roomslist/'


@method_decorator(staff_member_required, name='dispatch')
class MovieCreateView(CreateView):
    """
    Create Movie. Only for administrators.
    """
    model = Movie
    template_name = 'edit.html'
    form_class = MovieCreateForm
    success_url = '/movieslist/'


@method_decorator(staff_member_required, name='dispatch')
class SessionCreateView(CreateView):
    """
    Create Session. Only for administrators.
    """
    model = Session
    template_name = 'edit.html'
    form_class = SessionCreateForm
    success_url = '/sessionslist/'


@method_decorator(staff_member_required, name='dispatch')
class SessionsListView(ListView):
    """
    List of sessions
    """
    model = Session
    paginate_by = 10
    template_name = 'session-list.html'
    today = dt.now().date()
    queryset = Session.objects.filter(date_finish__gte=today).annotate(
        tickets=Count('session_tickets')
    )


@method_decorator(staff_member_required, name='dispatch')
class RoomListView(ListView):
    """
    List of rooms
    """
    model = Room
    paginate_by = 10
    template_name = 'room-list.html'
    today = dt.now().date()
    queryset = Room.objects.all().annotate(
        tickets=Count('room_sessions__session_tickets')
    )


@method_decorator(staff_member_required, name='dispatch')
class RoomListView(ListView):
    """
    List of rooms
    """
    model = Room
    paginate_by = 10
    template_name = 'room-list.html'
    today = dt.now().date()
    queryset = Room.objects.all().annotate(
        tickets=Count('room_sessions__session_tickets')
    )


@method_decorator(staff_member_required, name='dispatch')
class MovieListView(ListView):
    """
    List of rooms
    """
    model = Movie
    paginate_by = 10
    template_name = 'movie-list.html'
    queryset = Movie.objects.all()


@method_decorator(staff_member_required, name='dispatch')
class SessionUpdate(UpdateView):
    """
    Update session. Only for administrators.
    """
    model = Session
    template_name = 'edit.html'
    success_url = '/sessionslist/'
    fields = [
        'movie',
        'room',
        'time_start',
        'time_finish',
        'date_start',
        'date_finish',
        'price',
    ]


@method_decorator(staff_member_required, name='dispatch')
class MovieUpdate(UpdateView):
    """
    Update Movie. Only for administrators.
    """
    model = Movie
    template_name = 'edit.html'
    success_url = '/movieslist/'
    fields = [
        'title',
        'description',
        'duration',
        'director',
        'year',
        'poster',
    ]


@method_decorator(staff_member_required, name='dispatch')
class RoomUpdate(UpdateView):
    """
    Update Room. Only for administrators.
    """
    model = Room
    template_name = 'edit.html'
    success_url = '/roomslist/'
    fields = [
        'title',
        'seats_count',
    ]
