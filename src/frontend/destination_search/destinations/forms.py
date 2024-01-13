from django import forms
from django_select2 import forms as s2forms
from .models import CoreLocations


class SelectMultipleLocationsWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "location_id__icontains",
        "city__icontains",
    ]


class SelectSingleLocationWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "location_id__icontains",
        "city__icontains",
    ]


class TravellersInputForm(forms.Form):
    previous_locations = forms.ModelMultipleChoiceField(
        queryset=CoreLocations.objects.only('location_id', 'city'),
        to_field_name='location_id',
        widget=SelectMultipleLocationsWidget(attrs={
            'data-placeholder': 'Select location(s)...',
            'data-minimum-input-length': 1
        }),
        required=True,
        help_text="Search for locations you have previously visited. You can select multiple previous_locations. We'll use this information to compute the relevance of destinations for you."
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="Select the start date of your travel"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="Select the end date of your travel"
    )
    start_location = forms.CharField(help_text="Enter your start location. We'll use this to compute the distance to each destination.")


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