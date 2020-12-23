from datetime import datetime as dt, date, timedelta
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from django_cinema.settings import DURATION_OF_BREAKS


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
        return f'{self.full_name} {self.phone}'


class Room(models.Model):
    """
    Cinema room
    """
    title = models.CharField(max_length=120, unique=True)
    seats_count = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.title}  / {self.seats_count} seats'


class Movie(models.Model):
    """
    Movie
    """
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    duration = models.IntegerField(help_text='Movie duration time (minutes)')
    director = models.CharField(max_length=120, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    poster = models.ImageField(
        verbose_name='Poster',
        upload_to='media/posters',
        default='media/default.png',
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
    time_finish = models.TimeField(null=True, blank=True, )
    date_start = models.DateField()
    date_finish = models.DateField(null=True, blank=True, )
    price = models.FloatField()

    def save(self, *args, **kwargs):
        # the session does not change after buying tickets
        if self.session_tickets.count():
            raise ValidationError('The session has a ticket')
        # autofill the finish time field
        if not self.time_finish:
            td = timedelta(minutes=self.movie.duration + DURATION_OF_BREAKS)
            time = dt.combine(date.min, self.time_start)
            self.time_finish = (time + td).time()
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
                f'Should be more then {self.movie.duration_format}'
            )

        # sessions should not overlap
        sessions_start = Session.objects.filter(
            date_start__gte=self.date_start,
            date_start__lte=self.date_finish,
            room=self.room
        )
        sessions_finish = Session.objects.filter(
            date_finish__gte=self.date_start,
            date_finish__lte=self.date_finish,
            room=self.room
        )
        sessions = sessions_start | sessions_finish

        for session in sessions:
            if session.time_start <= self.time_start <= session.time_finish:
                raise ValidationError(
                    f"start time isn't free at {session.date_start} - "
                    f"{session.date_finish} / {session.movie.title}"
                )
            if session.time_start <= self.time_finish <= session.time_finish:
                raise ValidationError(f"finish time isn't free")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.room.title} {self.time_start}-{self.time_finish} " \
               f"/${self.price} / {self.movie.title} / {self.date_start} - " \
               f"{self.date_finish}"


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
        today = dt.now().date()
        tomorrow = today + timedelta(days=1)

        day_session_tickets = Ticket.objects.filter(
            date=self.date,
            session=self.session
        )
        # the count of tickets should not exceed
        # the count of seats in the room
        if day_session_tickets.count() >= self.session.room.seats_count:
            raise ValidationError('no more seats for new tickets')
        if self.date > self.session.date_finish \
                or self.date < self.session.date_start:
            raise ValidationError(
                f'ticket date must be in {self.session.date_start} - '
                f'{self.session.date_finish}'
            )
        if tomorrow < self.date < today:
            raise ValidationError('wrong date')
        if self.date == today and self.session.date_start < dt.now().time():
            raise ValidationError('wrong time')

        super().save(*args, **kwargs)

    class Meta:
        unique_together = (("date", "session", "seat_number"),)

    def __str__(self):
        return f"{self.session.movie.title}  [{self.date} " \
               f"{self.session.time_start}] ( #{self.seat_number} )" \
               f" user: {self.user.get_full_name()}"
