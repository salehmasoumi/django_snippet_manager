from django.urls import path
from . import views

app_name = 'favorites'

urlpatterns = [
    path('<slug:slug>/toggle/', views.toggle_favorite, name='toggle'),
]
