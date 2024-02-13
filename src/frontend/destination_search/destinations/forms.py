from django import forms
from .models import CoreCategories, CoreDimensions
import ast


class TravellersInputForm(forms.Form):

    previous_locations = forms.CharField(
        widget=forms.SelectMultiple(attrs={'class': 'input-box'}),
        required=True,
        label='Previous destinations',
        help_text=(
            "Search for (multiple) destinations you have previously visited."
            " We'll use this information to compute the relevance of new destinations for you."
            " If you cannot find your previous destination, you may select the country."
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
            return [location for location in ast.literal_eval(previous_locations)]
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

    min_population = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False,
        label='Population',
        help_text='Population of the destination.'
    )
    max_population = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False,
    )

    min_temperature = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False,
        label='Temperature',
        help_text='Temperature range at the destination. This filter just checks that the range it not exceeded. The actual range can be much more narrow.'
    )
    max_temperature = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False,
    )

    min_travel_cost = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False,
        label='Travel cost',
        help_text='Flight cost from start location (reference) to destination.'
    )
    max_travel_cost = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False,
    )

    min_accommodation_cost = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False,
        label='Accommodation cost',
        help_text='Hote prices at the destination for one night.'
    )
    max_accommodation_cost = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False,
    )

    min_best_reachability = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False,
        label='Reachability',
        help_text='Best reachability (using the fastest mean of transport).'
    )
    max_best_reachability = forms.FloatField(
        widget=forms.HiddenInput(),
        required=False,
    )

    mode_of_transport = forms.MultipleChoiceField(
        choices=[], # Populated in __init__
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Mode of transport',
        help_text='The destination has to be reachable by at least one of the selected options.'
    )

    def __init__(self, *args, **kwargs):
        super(FiltersForm, self).__init__(*args, **kwargs)

        modes_of_transport = (
            CoreDimensions.objects
            .filter(category_id=6)
            .values('dimension_id', 'dimension_name', 'icon_url')
        )
        # Clean up and store to access from template
        self.modes_of_transport_data = [
            {
                'dimension': f"dim_{mode['dimension_id']}",
                'name': mode['dimension_name'],
                'icon_url': mode['icon_url']
            }
            for mode in modes_of_transport
        ]
        # Set choices
        self.fields['mode_of_transport'].choices = [
            (mode['dimension'], mode['name'])
            for mode in self.modes_of_transport_data
        ]


class PreferencesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(PreferencesForm, self).__init__(*args, **kwargs)
        self.categories = []
        for category in CoreCategories.objects.exclude(category_id=0).order_by('display_order'):
            self.add_category(category.category_id, category.category_name, category.description)
        self.add_category(999, 'Distance from start location', distance_from_start_location_description)

    def add_category(self, category_id, category_name, category_description):
        self.fields[f'importance_{category_id}'] = forms.FloatField(
            required=False,
            widget=forms.HiddenInput()
        )
        self.fields[f'direction_{category_id}'] = forms.BooleanField(
            required=False,
            widget=forms.HiddenInput(attrs={'class': 'preferences-checkbox'})
        )
        self.categories.append({
            'category_id': category_id,
            'category_name': category_name,
            'fields': {
                'importance': self[f'importance_{category_id}'],
                'direction': self[f'direction_{category_id}']
            },
            'category_description': category_description
        })

    def get_categories(self):
        return self.categories

    def clean(self):
        cleaned_data = super().clean()

        for category in self.categories:
            category_id = category['category_id']

            direction_field = f'direction_{category_id}'
            if direction_field not in cleaned_data or cleaned_data[direction_field] is None:
                cleaned_data[direction_field] = False

            importance_field = f'importance_{category_id}'
            if importance_field not in cleaned_data or cleaned_data[importance_field] is None:
                cleaned_data[importance_field] = 0.5

        return cleaned_data


class SearchLocationForm(TravellersInputForm):
    location = forms.IntegerField(
        widget=forms.Select(attrs={'class': 'input-box'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(SearchLocationForm, self).__init__(*args, **kwargs)
        self.fields.pop('previous_locations')

        for field in ['start_date', 'end_date', 'start_location', 'start_location_lat', 'start_location_lon']:
            self.fields[field].required = False
