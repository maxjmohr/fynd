from django import forms
from django_select2 import forms as s2forms
from .models import CoreLocations

class SelectMultipleLocationsWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "location_id__icontains",
        "city__icontains",
    ]

class PreviousLocationsForm(forms.Form):
    locations = forms.ModelMultipleChoiceField(
        queryset=CoreLocations.objects.only('location_id', 'city'),
        to_field_name='location_id',
        widget=SelectMultipleLocationsWidget(attrs={
            'data-placeholder': 'Select location(s)...',
            'data-minimum-input-length': 1
        }),
        required=False
    )


class SelectSingleLocationWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "location_id__icontains",
        "city__icontains",
    ]

class SearchLocationForm(forms.Form):
    location = forms.ModelChoiceField(
        queryset=CoreLocations.objects.only('location_id', 'city'),
        to_field_name='location_id',
        widget=SelectSingleLocationWidget(attrs={
            'data-placeholder': 'Select location...',
            'data-minimum-input-length': 1
        }),
        required=True
    )