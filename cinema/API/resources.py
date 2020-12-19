from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication

from cinema.API.serialisers import RoomSerializer
from cinema.models import Room


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    authentication_classes = [BasicAuthentication, ]
