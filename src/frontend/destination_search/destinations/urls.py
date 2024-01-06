from django.urls import path

from .views import HomePageView,  LocationsListView

urlpatterns = [
    path("list/",  LocationsListView.as_view(), name="locations_list"),
    path("", HomePageView.as_view(), name="home"),
]