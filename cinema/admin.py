from django.contrib import admin

# Register your models here.
from django.utils.safestring import mark_safe

from .models import Ticket, CinemaUser, Movie, Room, Session

# class ProductAdmin(admin.ModelAdmin):
#     readonly_fields = ["preview"]
#
#     def preview(self, obj):
#         return mark_safe(f'<img src="{obj.image.url}" height="200">')


admin.site.register(Ticket)
admin.site.register(CinemaUser)
admin.site.register(Movie)
admin.site.register(Room)
admin.site.register(Session)
