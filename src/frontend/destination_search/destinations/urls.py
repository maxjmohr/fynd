from django.urls import path

from .views import HomePageView, LocationsListView, LocationDetailView

urlpatterns = [
    path('list/',  LocationsListView.as_view(), name='locations_list'),
    path('', HomePageView.as_view(), name='home'),
    path('location/<int:location_id>/', LocationDetailView.as_view(), name='location_detail'),
]