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
    time_start = models.DateTimeField()
    time_finish = models.DateTimeField()
    price = models.FloatField()

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        null=False,
        related_name='room_sessions',
    )

    def save(self, *args, **kwargs):
        # finish date must be similar start date
        if self.time_start.year != self.time_finish.year or \
                self.time_start.month != self.time_finish.month or \
                self.time_start.day != self.time_finish.day:
            raise ValidationError('Wrong end date')

        # finish time must be bigger than start time
        if self.time_start >= self.time_finish:
            raise ValidationError('Wrong end time')

        # session duration must be longer or equal than movie duration
        session_duration = (self.time_finish - self.time_start).seconds // 60
        if self.movie.duration > session_duration:
            raise ValidationError(
                f'session too short for {self.movie.title} movie. '
                f'Should be more then {self.movie.duration_format}')

        # sessions should not overlap
        sessions = Session.objects.filter(
            time_start__year=self.time_start.year,
            time_start__month=self.time_start.month,
            time_start__day=self.time_start.day,
            room=self.room
        )
        session_times = [(s.time_start, s.time_finish) for s in sessions]
        for i in session_times:
            if i[0] <= self.time_start <= i[1]:
                raise ValidationError(f"start time isn't free")
            if i[0] <= self.time_finish <= i[1]:
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

    def save(self, *args, **kwargs):
        session = self.session
        if session.session_tickets.count() >= session.room.seats_count:
            raise ValidationError('no more seats for new tickets')
        super().save(*args, **kwargs)
