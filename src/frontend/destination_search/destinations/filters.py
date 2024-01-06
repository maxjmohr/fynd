import django_filters
from .models import CoreLocations

class LocationsFilterset(django_filters.FilterSet):
    class Meta:
        model = CoreLocations
        fields = ['country']