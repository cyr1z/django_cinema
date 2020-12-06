from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class CinemaUser(AbstractUser):
    """
    Customised Django User Model
    Add avatar, telegram name and telegram id
    unique combinations of First Name and Last Name
    """
    is_active = models.BooleanField(
        default=True
    )
    phone = models.CharField(
        max_length=120
    )

    @property
    def full_name(self):
        if self.get_full_name():
            return self.get_full_name()
        else:
            return self.username

    class Meta:
        unique_together = ["first_name", "last_name"]
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.get_full_name()
