from datetime import datetime as dt, date, timedelta

from rest_framework import viewsets, generics, status, serializers
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser, \
    SAFE_METHODS, BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from cinema.API.serialisers import RoomSerializer, UserSerializer, \
    MovieSerializer, SessionSerializer, TicketSerializer, \
    TicketAdminSerializer, RegisterSerializer, SessionAdminSerializer
from cinema.models import Room, CinemaUser, Movie, Session, Ticket
from django_cinema.settings import DURATION_OF_BREAKS


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class AuthorizedCreate(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.method == 'POST'


class Register(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return request.method == 'POST'


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [IsAdminUser | ReadOnly]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        tickets = Ticket.objects.filter(
            session__room=instance.session,
            date__gte=dt.now().date()).count()
        if tickets:
            raise serializers.ValidationError(
                {"room_tickets": "The room has a ticket"})
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    # TODO: delete

    serializer_class = UserSerializer
    queryset = CinemaUser.objects.all()
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [IsAdminUser | Register]

    def get_serializer_class(self):
        print(self.request.method)
        if hasattr(self.request, 'method'):
            if self.request.method in SAFE_METHODS:
                return UserSerializer
            elif self.request.method == 'POST':
                return RegisterSerializer
            else:
                return UserSerializer


class MovieViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [IsAdminUser | ReadOnly]


class SessionViewSet(viewsets.ModelViewSet):
    serializer_class = SessionSerializer
    queryset = Session.objects.all()
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [IsAdminUser | ReadOnly]

    def get_serializer_class(self):
        print(self.request.method)
        if hasattr(self.request, 'method'):
            if self.request.method in SAFE_METHODS:
                return SessionSerializer
            elif self.request.method in ('POST', "PUT", "PATCH"):
                return SessionAdminSerializer
            else:
                return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        obj = serializer.validated_data

        # autofill the finish time field
        movie_duration = obj.get('movie').duration
        session_time_finish = obj.get('time_finish')
        session_time_start = obj.get('time_start')
        session_date_finish = obj.get('date_finish')
        session_date_start = obj.get('date_start')
        movie_title = obj.get('movie').title
        movie_duration_format = obj.get('movie').duration_format
        room = obj.get('room')

        if instance.session_tickets.count():
            raise serializers.ValidationError(
                {"session_tickets": "The session has a ticket"})

        if not session_time_finish:
            td = timedelta(minutes=movie_duration + DURATION_OF_BREAKS)
            time = dt.combine(date.min, session_time_start)
            session_time_finish = obj['time_finish'] = (time + td).time()
            serializer.validated_data['time_finish'] = session_time_finish

        # finish time must be bigger than start time
        if session_time_start >= session_time_finish:
            raise serializers.ValidationError(
                {"time_finish": "finish time smaller then start."})

        # session duration must be longer or equal than movie duration
        finish = dt.combine(date.min, session_time_finish)
        start = dt.combine(date.min, session_time_start)
        session_duration = (finish - start).seconds // 60
        if movie_duration > session_duration:
            time_short_err = f'session too short for {movie_title}' \
                             f' movie. Should be more then ' \
                             f'{movie_duration_format}'
            raise serializers.ValidationError(
                {"time_finish": time_short_err})

        # sessions should not overlap
        sessions_start = Session.objects.filter(
            date_start__gte=str(session_date_start),
            date_start__lte=str(session_date_finish),
            room=room
        ).exclude(id=instance.id)
        sessions_finish = Session.objects.filter(
            date_finish__gte=session_date_start,
            date_finish__lte=session_date_finish,
            room=room
        ).exclude(id=instance.id)
        sessions = sessions_start | sessions_finish

        for session in sessions:
            if session.time_start <= session_time_start <= session.time_finish:
                time_err = f"start time isn't free at {session.date_start}" \
                           f" - {session.date_finish} / {session.movie.title}"
                raise serializers.ValidationError(
                    {"time_finish": time_err})
            if session.time_start <= session_time_finish <= session.time_finish:
                time_err = f"finish time isn't free at {session.date_start}" \
                           f" - {session.date_finish} / {session.movie.title}"
                raise serializers.ValidationError(
                    {"time_finish": time_err})
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data)

        obj = serializer.validated_data

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
            serializer.validated_data['time_finish'] = session_time_finish

        # finish time must be bigger than start time
        if session_time_start >= session_time_finish:
            raise serializers.ValidationError(
                {"time_finish": "finish time smaller then start."})

        # session duration must be longer or equal than movie duration
        finish = dt.combine(date.min, session_time_finish)
        start = dt.combine(date.min, session_time_start)
        session_duration = (finish - start).seconds // 60
        if movie_duration > session_duration:
            time_short_err = f'session too short for {movie_title}' \
                             f' movie. Should be more then ' \
                             f'{movie_duration_format}'
            raise serializers.ValidationError({"time_finish": time_short_err})

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
                raise serializers.ValidationError({"time_start": time_err})
            if session.time_start <= session_time_finish <= session.time_finish:
                time_err = f"finish time isn't free at {session.date_start}" \
                           f" - {session.date_finish} / {session.movie.title}"
                raise serializers.ValidationError({"time_finish": time_err})

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [
        IsAuthenticated & ReadOnly | IsAdminUser | AuthorizedCreate]

    def get_queryset(self):
        queryset = Ticket.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        print(self.request.method)
        if hasattr(self.request, 'method'):
            if self.request.method == 'GET':
                return TicketSerializer
            if self.request.method == 'POST':
                return TicketAdminSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data)

        obj = serializer.validated_data

        session = obj.get('session')
        user = obj.get('user')
        ticket_date = obj.get('date')
        seat_number = obj.get('seat_number')
        today = dt.now().date()
        tomorrow = today + timedelta(days=1)
        now = dt.now()
        bought_seats = session.session_tickets.filter(date=ticket_date)
        bought_seats_numbers = set(i.seat_number for i in bought_seats)
        all_seats = set(range(1, session.room.seats_count + 1))
        free_seats = all_seats - bought_seats_numbers

        # ticket must have the free seat
        if seat_number not in free_seats:
            raise serializers.ValidationError(
                {"seats_number": 'Invalid seat number'}
            )

        # ticket date must  be in session period
        if session.date_start > ticket_date or session.date_finish < ticket_date:
            raise serializers.ValidationError(
                {"seats_number": 'Invalid session date'}
            )

        # ticket day must be tomorrow or today
        if tomorrow < ticket_date or ticket_date < today:
            raise serializers.ValidationError(
                {"seats_number": 'wrong date'}
            )

        # ticket time must be greater than now
        if date == today and session.time_start < now.time():
            raise serializers.ValidationError(
                {"seats_number": 'wrong time'}
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class TodaySessionViewSet(generics.ListAPIView, ViewSet):
    serializer_class = SessionSerializer
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [ReadOnly]

    def get_queryset(self):
        """
        obtaining information about all sessions for today,
        which begin at a certain period of time and / or go in a
        particular room

        /today_session_api/?min_time=12:00:00&max_time=22:00:00&room=1
        """
        today = dt.now().date()

        queryset = Session.objects.filter(
            date_finish__gte=today,
            date_start__lte=today,
        )
        minimum_time = dt.strptime(
            self.request.query_params.get('min_time', '00:00:00'),
            "%H:%M:%S").time()
        queryset = queryset.filter(time_start__gte=minimum_time)

        maximum_time = dt.strptime(
            self.request.query_params.get('max_time', '23:59:59'),
            "%H:%M:%S").time()
        queryset = queryset.filter(time_start__lte=maximum_time)
        room = self.request.query_params.get('room', None)
        if room is not None:
            queryset = queryset.filter(room__id=room)
        return queryset
