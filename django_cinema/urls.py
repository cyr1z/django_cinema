"""django_cinema URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from cinema.views import Register, UserLogout, UserLogin, SessionsView, \
    TomorrowSessionsView, SessionDetailView, TicketsListView, RoomCreateView, \
    MovieCreateView, SessionCreateView

urlpatterns = [
    path('', SessionsView.as_view(), name="sessions"),
    path('tomorrow/', TomorrowSessionsView.as_view(), name="tomorrow"),
    path('session/<int:pk>/', SessionDetailView.as_view(), name='session'),
    path('accounts/login/', UserLogin.as_view(), name="login"),
    path('accounts/logout/', UserLogout.as_view(), name="logout"),
    path('accounts/register/', Register.as_view(), name="register"),
    path('tickets/', TicketsListView.as_view(), name="tickets"),
    path('createroom/', RoomCreateView.as_view(), name="createroom"),
    path('createmovie/', MovieCreateView.as_view(), name="createmovie"),
    path('createsession/', SessionCreateView.as_view(), name="createsession"),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
]
