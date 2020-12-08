from datetime import datetime as dt, date

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class CinemaUser(AbstractUser):
    """
    Customised Django User Model
    Add phone
    """

    phone = models.CharField(
        max_length=20
    )

    @property
    def full_name(self):
        if self.get_full_name():
            return self.get_full_name()
        else:
            return self.username

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.get_full_name()


class Room(models.Model):
    """
    Cinema room
    """

    title = models.CharField(max_length=120)
    seats_count = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.title} room / {self.seats_count} seats'


class Movie(models.Model):
    """
    Movie
    """

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    duration = models.IntegerField(help_text='Movie duration time (minutes)')
    poster = models.ImageField(
        verbose_name='Poster',
        upload_to='static/posters',
        default='static/default.png',
        null=True,
        blank=True
    )

    @property
    def duration_format(self):
        if self.duration // 60:
            return f'{self.duration // 60}h. {self.duration % 60}m.'
        return f'{self.duration}m.'

    def __str__(self):
        return f"{self.title} / {self.duration_format}"


class Session(models.Model):
    """
    Session
    """

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        null=True,
        related_name='movie_sessions'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        null=False,
        related_name='room_sessions',
    )
    time_start = models.TimeField()
    time_finish = models.TimeField()
    date_start = models.DateField()
    date_finish = models.DateField(null=True, blank=True, )
    price = models.FloatField()

    def save(self, *args, **kwargs):

        # finish time must be bigger than start time
        if self.time_start >= self.time_finish:
            raise ValidationError('Wrong end time')

        # session duration must be longer or equal than movie duration
        finish = dt.combine(date.min, self.time_finish)
        start = dt.combine(date.min, self.time_start)
        session_duration = (finish - start).seconds // 60
        if self.movie.duration > session_duration:
            raise ValidationError(
                f'session too short for {self.movie.title} movie. '
                f'Should be more then {self.movie.duration_format}')

        # sessions should not overlap
        sessions_start = Session.objects.filter(
            date_start__gte=self.date_start,
            date_start__lte=self.date_finish,
            room=self.room
        )
        sessions_finish = Session.objects.filter(
            date_fininsh__gte=self.date_start,
            date_finish__lte=self.date_finish,
            room=self.room
        )
        sessions = sessions_start | sessions_finish

        for session in sessions:
            if session.time_start <= self.time_start <= session.time_finish:
                raise ValidationError(
                    f"start time isn't free [ {session.date_start}"
                    f" {session.date_finish if session.date_finish else ''} ]"
                    f"/ {session.title}")
            if session.time_start <= self.time_finish <= session.time_finish:
                raise ValidationError(f"finish time isn't free")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.room.title} {self.time_start}-{self.time_finish} " \
               f"/${self.price}"


class Ticket(models.Model):
    """
    Ticket
    """
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        null=True,
        related_name='session_tickets'
    )
    user = models.ForeignKey(
        CinemaUser,
        on_delete=models.CASCADE,
        null=True,
        related_name='user_tickets'
    )
    date = models.DateField()
    seat_number = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        day_session_tickets = Ticket.objects.filter(date=self.date,
                                                    session=self.session)
        if day_session_tickets.count() >= self.session.room.seats_count:
            raise ValidationError('no more seats for new tickets')
        super().save(*args, **kwargs)

    class Meta:
        unique_together = (("date", "session", "seat_number"),)
