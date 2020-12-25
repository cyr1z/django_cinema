import re
from datetime import datetime as dt, timedelta, date

from django.contrib import messages
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

from django_cinema.settings import DATE_REGEXP, DEFAULT_SESSION_ORDERING, \
    SESSION_ORDERINGS, DURATION_OF_BREAKS


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

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', DEFAULT_SESSION_ORDERING)
        # validate ordering here
        if ordering not in SESSION_ORDERINGS:
            ordering = DEFAULT_SESSION_ORDERING
        return ordering

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

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', DEFAULT_SESSION_ORDERING)
        # validate ordering here
        if ordering not in SESSION_ORDERINGS:
            ordering = DEFAULT_SESSION_ORDERING
        return ordering

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
        # Add date
        date = self.get_date()

        # add free seats and tickets count
        bought_seats = self.object.session_tickets.filter(date=date)
        bought_seats_numbers = set(i.seat_number for i in bought_seats)
        all_seats = set(range(1, self.object.room.seats_count + 1))
        free_seats = list(all_seats - bought_seats_numbers)
        free_seats_count = len(free_seats)
        session_tickets_count = len(bought_seats_numbers)

        # set form inputs values, choices and  parameters
        form = BuyTicketForm(self.request.POST or None)
        form.fields['date'].initial = dt.strftime(date, '%Y-%m-%d')
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

    def post(self, *args, **kwargs):

        form = BuyTicketForm(self.request.POST)
        if form.is_valid():
            data = dict(form.cleaned_data)
            try:
                session = Session.objects.get(id=data.get('session'))
            except:
                messages.error(self.request, 'Invalid session')
                return HttpResponseRedirect(
                    self.request.META.get('HTTP_REFERER'))

            date = data.get('date')
            seat_numbers_str = data.get('seat_numbers')
            seat_numbers = set(int(i) for i in seat_numbers_str)
            user = self.request.user
            today = dt.now().date()
            tomorrow = today + timedelta(days=1)
            now = dt.now()
            # ticket must have the free seat
            bought_seats = session.session_tickets.filter(date=date)
            bought_seats_numbers = set(i.seat_number for i in bought_seats)
            all_seats = set(range(1, session.room.seats_count + 1))
            free_seats = all_seats - bought_seats_numbers
            if not set(seat_numbers).issubset(free_seats):
                messages.error(self.request, 'Invalid seats')
                return HttpResponseRedirect(
                    self.request.META.get('HTTP_REFERER'))

            # ticket date must  be in session period
            if session.date_start > date or session.date_finish < date:
                messages.error(self.request, 'Invalid session date')
                return HttpResponseRedirect(
                    self.request.META.get('HTTP_REFERER'))

            # ticket day must be tomorrow or today
            if tomorrow < date or date < today:
                messages.error(self.request, 'wrong date')
                return HttpResponseRedirect(
                    self.request.META.get('HTTP_REFERER'))

            # ticket time must be greater than now
            if date == today and session.time_start < now.time():
                messages.error(self.request, 'wrong time')
                return HttpResponseRedirect(
                    self.request.META.get('HTTP_REFERER'))

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
        else:
            err = form.errors.get('__all__')
            messages.error(self.request, err)
            return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


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
            'tickets_count': tickets_count.get('id__count'),
            'money_sum': money_sum.get('session__price__sum'),
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

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        obj = form.cleaned_data

        movie_duration = obj.get('movie').duration
        session_time_finish = obj.get('time_finish')
        session_time_start = obj.get('time_start')
        session_date_finish = obj.get('date_finish')
        session_date_start = obj.get('date_start')
        movie_title = obj.get('movie').title
        movie_duration_format = obj.get('movie').duration_format
        room = obj.get('room')

        # autofill the finish time field
        if not session_time_finish:
            td = timedelta(minutes=movie_duration + DURATION_OF_BREAKS)
            time = dt.combine(date.min, session_time_start)
            session_time_finish = obj['time_finish'] = (time + td).time()
            form.cleaned_data['time_finish'] = session_time_finish

        # finish time must be bigger than start time
        if session_time_start >= session_time_finish:
            messages.error(self.request, 'Wrong end time')
            return HttpResponseRedirect(
                self.request.META.get('HTTP_REFERER'))

        # session duration must be longer or equal than movie duration
        finish = dt.combine(date.min, session_time_finish)
        start = dt.combine(date.min, session_time_start)
        session_duration = (finish - start).seconds // 60
        if movie_duration > session_duration:
            time_short_err = f'session too short for {movie_title}' \
                             f' movie. Should be more then ' \
                             f'{movie_duration_format}'
            messages.error(self.request, time_short_err)
            return HttpResponseRedirect(
                self.request.META.get('HTTP_REFERER'))

        # sessions should not overlap
        sessions_start = Session.objects.filter(
            date_start__gte=str(session_date_start),
            date_start__lte=str(session_date_finish),
            room=room
        )
        sessions_finish = Session.objects.filter(
            date_finish__gte=session_date_start,
            date_finish__lte=session_date_finish,
            room=room
        )
        sessions = sessions_start | sessions_finish

        for session in sessions:
            if session.time_start <= session_time_start <= session.time_finish:
                time_err = f"start time isn't free at {session.date_start}" \
                           f" - {session.date_finish} / {session.movie.title}"
                messages.error(self.request, time_err)
                return HttpResponseRedirect(
                    self.request.META.get('HTTP_REFERER'))
            if session.time_start <= session_time_finish <= session.time_finish:
                time_err = f"finish time isn't free at {session.date_start}" \
                           f" - {session.date_finish} / {session.movie.title}"
                messages.error(self.request, time_err)
                return HttpResponseRedirect(
                    self.request.META.get('HTTP_REFERER'))

        return super().form_valid(form)


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
class MovieListView(ListView):
    """
    List of Movie
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

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        obj = form.cleaned_data

        # autofill the finish time field
        movie_duration = obj.get('movie').duration
        session_time_finish = obj.get('time_finish')
        session_time_start = obj.get('time_start')
        session_date_finish = obj.get('date_finish')
        session_date_start = obj.get('date_start')
        movie_title = obj.get('movie').title
        movie_duration_format = obj.get('movie').duration_format
        room = obj.get('room')

        try:
            session = self.object
        except:
            messages.error(self.request, 'Invalid session')
            return HttpResponseRedirect(
                self.request.META.get('HTTP_REFERER'))

        if session.session_tickets.count():
            messages.error(self.request, 'The session has a ticket')
            return HttpResponseRedirect(
                self.request.META.get('HTTP_REFERER'))

        if not session_time_finish:
            td = timedelta(minutes=movie_duration + DURATION_OF_BREAKS)
            time = dt.combine(date.min, session_time_start)
            session_time_finish = obj['time_finish'] = (time + td).time()
            form.cleaned_data['time_finish'] = session_time_finish

        # finish time must be bigger than start time
        if session_time_start >= session_time_finish:
            messages.error(self.request, 'Wrong end time')
            return HttpResponseRedirect(
                self.request.META.get('HTTP_REFERER'))

        # session duration must be longer or equal than movie duration
        finish = dt.combine(date.min, session_time_finish)
        start = dt.combine(date.min, session_time_start)
        session_duration = (finish - start).seconds // 60
        if movie_duration > session_duration:
            time_short_err = f'session too short for {movie_title}' \
                             f' movie. Should be more then ' \
                             f'{movie_duration_format}'
            messages.error(self.request, time_short_err)
            return HttpResponseRedirect(
                self.request.META.get('HTTP_REFERER'))

        # sessions should not overlap
        sessions_start = Session.objects.filter(
            date_start__gte=str(session_date_start),
            date_start__lte=str(session_date_finish),
            room=room
        ).exclude(id=session.id)
        sessions_finish = Session.objects.filter(
            date_finish__gte=session_date_start,
            date_finish__lte=session_date_finish,
            room=room
        ).exclude(id=session.id)

        sessions = sessions_start | sessions_finish

        for session in sessions:
            if session.time_start <= session_time_start <= session.time_finish:
                time_err = f"start time isn't free at {session.date_start}" \
                           f" - {session.date_finish} / {session.movie.title}"
                messages.error(self.request, time_err)
                return HttpResponseRedirect(
                    self.request.META.get('HTTP_REFERER'))
            if session.time_start <= session_time_finish <= session.time_finish:
                time_err = f"finish time isn't free at {session.date_start}" \
                           f" - {session.date_finish} / {session.movie.title}"
                messages.error(self.request, time_err)
                return HttpResponseRedirect(
                    self.request.META.get('HTTP_REFERER'))

        return super().form_valid(form)


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

    def form_valid(self, form):

        """If the form is valid, save the associated model."""
        obj = form.cleaned_data
        room = self.object
        tickets = Ticket.objects.filter(
            session__room=room,
            date__gt=dt.now().date()).count()
        if tickets:
            messages.error(self.request, "The room has a ticket")
            return HttpResponseRedirect(
                self.request.META.get('HTTP_REFERER'))

        return super().form_valid(form)
