from rest_framework import serializers

from cinema.models import Movie, Session, Room, Ticket, CinemaUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'id',
            'phone',
        ]


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['title', 'seats_count', ]


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = [
            'title',
            'description',
            'poster',
            'year',
            'duration',
            'director'
        ]


class SessionSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()
    room = RoomSerializer()

    # session_tickets = TicketSerializer(many=True)

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


class TicketSerializer(serializers.ModelSerializer):
    session = SessionSerializer()
    user = UserSerializer()

    class Meta:
        model = Ticket
        fields = [
            'session',
            'user',
            'date',
            'seat_number',
        ]

#
# class TodaySessionSerializer(serializers.Serializer):
#     movie = MovieSerializer()
#     room = RoomSerializer()
#     time_start = serializers.TimeField()
#     time_finish = serializers.TimeField()
#     date_start = serializers.DateField()
#     date_finish = serializers.DateField()
#     price = serializers.FloatField()

    # session_tickets = TicketSerializer(many=True)

    # class Meta:
    #     model = Session
    #     fields = [
    #         'movie',
    #         'room',
    #         'time_start',
    #         'time_finish',
    #         'date_start',
    #         'date_finish',
    #         'price',
    #     ]
