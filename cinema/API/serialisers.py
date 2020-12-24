from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

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


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=CinemaUser.objects.all())]
    )

    password = serializers.CharField(write_only=True, required=True,
                                     validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CinemaUser
        fields = ('username', 'password', 'password2', 'email', 'first_name',
                  'last_name', 'phone')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = CinemaUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],

        )

        user.set_password(validated_data['password'])
        user.save()

        return user


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


class SessionAdminSerializer(serializers.ModelSerializer):

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


class TicketAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            'session',
            'user',
            'date',
            'seat_number',
        ]
