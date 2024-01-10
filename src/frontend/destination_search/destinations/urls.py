from django.urls import path, include
from .views import HomePageView, LocationsListView, LocationDetailView, DiscoverView, SearchView, CompareView, AboutView

urlpatterns = [
    path("select2/", include("django_select2.urls")),
    path('list/',  LocationsListView.as_view(), name='locations_list'),
    path('', HomePageView.as_view(), name='home'),
    path('location/<int:location_id>/', LocationDetailView.as_view(), name='location_detail'),
    path('discover/', DiscoverView.as_view(), name='discover'),
    path('search/', SearchView.as_view(), name='search'),
    path('compare/', CompareView.as_view(), name='compare'),
    path('about/', AboutView.as_view(), name='about'),
]