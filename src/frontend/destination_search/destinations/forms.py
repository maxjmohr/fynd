from django import forms
from django_select2 import forms as s2forms
from .models import CoreLocations, CoreCategories


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
            'data-placeholder': 'Select destination(s)...',
            'data-minimum-input-length': 1
        }),
        required=True,
        label='Previous destinations',
        help_text=(
            "Search for destinations you have previously visited."
            " You can select multiple destinations."
            " We'll use this information to compute the relevance of new destinations for you."
        )
    )

    start_date = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
        label='Dates of travel',
        help_text=(
            "Select the start and end dates of your travel."
            " We'll use this to tailor some of our scores."
            " If you are not sure about the dates, you can also provide a borader range or just input the current date."
        ),
    )
    end_date = forms.CharField(widget=forms.HiddenInput(), required=True)
    
    start_location = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your start location...',
            'class': 'input-box'
        }),
        required=True,
        label='Start location',
        help_text=(
            "Enter your start location."
            " We'll use this to compute the distance to each destination and tailor some of our scores, e.g. the cost of travel and the reachability."
            " By now, our scores will work propely only for German locations."
        )
    )
    start_location_lat = forms.FloatField(widget=forms.HiddenInput(), required=False)
    start_location_lon = forms.FloatField(widget=forms.HiddenInput(), required=False)

    def clean_previous_locations(self):
        previous_locations = self.cleaned_data.get('previous_locations')
        if previous_locations is not None:
            # Convert the QuerySet to a list of location IDs
            return list(previous_locations.values_list('location_id', flat=True))
        return None

distance_from_start_location_description = "Distance (as the crow flies) from your start location to the destination."
class FiltersForm(forms.Form):
    min_distance = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False,
        label='Distance from start location',
        help_text=distance_from_start_location_description
    )
    max_distance = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False,
    )


class PreferencesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(PreferencesForm, self).__init__(*args, **kwargs)
        self.categories = []
        for category in CoreCategories.objects.exclude(category_id=0).order_by('display_order'):
            self.add_category(category.category_id, category.category_name, category.description)
        self.add_category(999, 'Distance from start location', distance_from_start_location_description)

    def add_category(self, category_id, category_name, category_description):
        self.fields[f'{category_name}_importance'] = forms.FloatField(
            required=False,
            widget=forms.HiddenInput()
        )
        self.fields[f'{category_name}_direction'] = forms.BooleanField(
            required=False,
            widget=forms.HiddenInput(attrs={'class': 'preferences-checkbox'})
        )
        self.categories.append({
            'category_id': category_id,
            'category_name': category_name,
            'fields': {
                'importance': self[f'{category_name}_importance'],
                'direction': self[f'{category_name}_direction']
            },
            'category_description': category_description
        })

    def get_categories(self):
        return self.categories


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