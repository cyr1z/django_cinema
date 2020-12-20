from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication

from cinema.API.serialisers import RoomSerializer, UserSerializer, \
    MovieSerializer, SessionSerializer, TicketSerializer, \
    TodaySessionSerializer
from cinema.models import Room, CinemaUser, Movie, Session, Ticket


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    authentication_classes = [BasicAuthentication, ]


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = CinemaUser.objects.all()
    authentication_classes = [BasicAuthentication, ]


class MovieViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()
    authentication_classes = [BasicAuthentication, ]


class SessionViewSet(viewsets.ModelViewSet):
    serializer_class = SessionSerializer
    queryset = Session.objects.all()
    authentication_classes = [BasicAuthentication, ]


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    queryset = Ticket.objects.all()
    authentication_classes = [BasicAuthentication, ]


class TodaySessionViewSet(viewsets.ModelViewSet):
    serializer_class = TodaySessionSerializer
    queryset = Session.objects.all()
    authentication_classes = [BasicAuthentication, ]
