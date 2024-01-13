from django import forms
from django_select2 import forms as s2forms
from datetime import datetime
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

    date_range = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'daterangepicker', 'placeholder': 'Select dates of travel...'}),
        help_text="Select the start and end dates of your travel. We'll use this to tailor the weather and price information. If you are not sure about the dates, you can also provide a borader range or just input the current date.",
        required=True
    )
    
    start_location = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter your start location...'}),
        help_text="Enter your start location. We'll use this to compute the distance to each destination and the cost of travel."
    )
    start_location_lat = forms.CharField(widget=forms.HiddenInput(), required=False)
    start_location_lon = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean_date_range(self):
        date_range = self.cleaned_data.get('date_range')
        if date_range:
            dates = date_range.split(' - ')
            if len(dates) != 2:
                raise forms.ValidationError("Invalid date range.")
            start_date, end_date = dates
            return start_date, end_date
        return None, None


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