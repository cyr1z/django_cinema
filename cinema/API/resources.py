from datetime import datetime as dt

from rest_framework import viewsets, generics
from rest_framework.authentication import BasicAuthentication
# from rest_framework.generics import get_object_or_404
# from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, \
    SAFE_METHODS, BasePermission
from rest_framework.viewsets import ViewSet

from cinema.API.serialisers import RoomSerializer, UserSerializer, \
    MovieSerializer, SessionSerializer, TicketSerializer, \
    SessionAdminSerializer, TicketAdminSerializer
from cinema.models import Room, CinemaUser, Movie, Session, Ticket


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class AuthorizedCreate(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.method == 'POST'


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [IsAdminUser | ReadOnly]


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = CinemaUser.objects.all()
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [IsAdminUser]


class MovieViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [IsAdminUser | ReadOnly]


class SessionViewSet(viewsets.ModelViewSet):
    serializer_class = SessionSerializer
    queryset = Session.objects.all()
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [ReadOnly]


class SessionAdminViewSet(viewsets.ModelViewSet):
    serializer_class = SessionAdminSerializer
    queryset = Session.objects.all()
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [IsAdminUser]


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    # ??
    queryset = Ticket.objects.all()
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [IsAuthenticated & ReadOnly]


class TicketAdminViewSet(viewsets.ModelViewSet):
    serializer_class = TicketAdminSerializer
    queryset = Ticket.objects.all()
    authentication_classes = [BasicAuthentication, ]
    permission_classes = [IsAdminUser | AuthorizedCreate]


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
