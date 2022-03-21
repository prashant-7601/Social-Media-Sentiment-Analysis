from django.contrib import admin
from django.urls import path
from Home import views

urlpatterns = [
    path("search", views.search, name="home"),
    path("", views.index, name="home"),
]
