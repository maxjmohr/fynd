from django.views import View
from django.views.generic import TemplateView, FormView
from django.views.generic.detail import DetailView
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.db.models import Q, Prefetch
from django.forms.models import model_to_dict
from .models import *
from .forms import *
from .compute_relevance import compute_relevance
from .compute_haversine import haversine
import numpy as np
import pandas as pd
from urllib.parse import urlencode
from django_pandas.io import read_frame
import json
import ast


def get_locations_for_select2():
    """Get locations for use in Select2."""
    locations = CoreLocations.objects.values('location_id', 'city', 'country', 'country_code')
    grouped_locations = []
    for location in locations:
        group = next((group for group in grouped_locations if group['text'] == location['country']), None)
        if group is None:
            group = {'id': location['country_code'], 'text': location['country'], 'isCountry': True, 'children': []}
            grouped_locations.append(group)
        group['children'].append({'id': location['location_id'], 'text': location['city'], 'isCountry': False, 'parent': location['country']})
    return json.dumps(grouped_locations)


def clean_id(s: pd.Series) -> pd.Series:
    """Get the value from an object."""
    return s.fillna(0).astype(int) #FIXME fillna is just a hot fix


def encode_url_parameters(params: dict) -> str:
    """Encode GET parameters for use in URL."""
    encoded_params = []
    for key, value in params.items():
        if isinstance(value, list):
            for item in value:
                encoded_params.append((key, item))
        else:
            encoded_params.append((key, value))
    return urlencode(encoded_params)

def get_comparison_params(session: dict) -> str:
    """Get comparison parameters for use in URL."""
    ti_form_data = session.get('travellers_input_form_data', {})
    params_to_include = ['start_date', 'end_date', 'start_location_lat', 'start_location_lon']
    params = {
        param_name: ti_form_data.get(param_name)
        for param_name in params_to_include
        if ti_form_data.get(param_name) is not None
    }
    return encode_url_parameters(params)


def create_hist_for_slider(data: pd.Series, bins:  int = 30):
    hist, bin_edges = np.histogram(data.dropna(), bins=30)  #FIXME drop missings?
    return {'heights': hist.tolist(), 'binLimits': bin_edges.tolist()}


def get_scores(
        start_date: str,
        end_date: str,
        start_location_lat: float|str,
        start_location_lon: float|str,
        location_id: int = None,
        retrieve_text: bool = False
    ):
    
    # Convert start and end date to datatime  ---------------------------------
    if start_date is not None:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
    else:
        start_date = pd.to_datetime('today')
        end_date = start_date + pd.Timedelta(days=365)
    
    # Get closest reference location for start location -----------------------
    if start_location_lat is not None and start_location_lon is not None:
        # Find closest reference location
        reference_start_locations = read_frame(
            CoreRefStartLocations
            .objects
            .values('location_id', 'city', 'country', 'lat', 'lon', 'mapped_start_airport')
        )
        reference_start_locations['distance'] = haversine(
            lon1=float(start_location_lon),
            lat1=float(start_location_lat),
            lon2=reference_start_locations['lon'].astype(float),
            lat2=reference_start_locations['lat'].astype(float)
        )
        reference_start_location = reference_start_locations.loc[
            reference_start_locations['distance'].idxmin()
        ].to_dict()
    else:
        # Use Frankfurt as reference start locations
        reference_start_location = model_to_dict(
            CoreRefStartLocations.objects.get(location_id=121553680)
        )

    # Get filtered scores -----------------------------------------------------

    # Filter
    query = CoreScores.objects.filter(
        Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
    )
    query = query.filter(
        ref_start_location_id__in=[-1, reference_start_location['location_id']]
    )

    if location_id is not None:
        query = query.filter(
            location_id__in=[location_id] if type(location_id) == int else location_id
        )

    # Define fileds to include in values() (negative selection)
    all_fields = [f.name for f in CoreScores._meta.get_fields()]
    exclude_fields = ['updated_at']
    include_fields = [f for f in all_fields if f not in exclude_fields]

    # Get as DataFrame
    scores = read_frame(query.values(*include_fields)).astype({'score': float, 'raw_value': float})

    # Convert 'start_date' and 'end_date' to datetime
    scores['start_date'] = pd.to_datetime(scores['start_date'])
    scores['end_date'] = pd.to_datetime(scores['end_date'])

    # Average scores for multiple time intervals ------------------------------

    # Calculate the number of days each score interval overlaps
    # with the given travel interval
    scores['overlap_days'] = scores.apply(
        lambda row: min(row['end_date'], end_date) - 
                    max(row['start_date'], start_date) + 
                    pd.Timedelta(days=1), 
        axis=1
    ).dt.days

    # Calculate the sum of the weighted scores
    value_cols = ['score', 'raw_value']
    for col in value_cols:
        scores[col] *= scores['overlap_days']
    scores = (
        scores
        .groupby(['location_id', 'category_id', 'dimension_id'])
        .agg({
            'score': lambda x: x.sum(skipna=False),
            'raw_value': lambda x: x.sum(skipna=False),
            'overlap_days': lambda x: x.sum(skipna=False)
        })
    )
    for col in value_cols:
        scores[col] /= scores['overlap_days']
    scores.drop(columns=['overlap_days'], inplace=True)
    scores.reset_index(inplace=True)

    # Get text ---------------------------------------------------------------
    if retrieve_text:
        if type(location_id) == list:
            raise ValueError('Text retrieval ony possible for one location_id.')
        else:
            #FIXME how to handle start and end date, since we cant average texts?
            texts = CoreTexts.objects.filter(
                Q(location_id=location_id)
                & Q(ref_start_location_id__in=[-1, reference_start_location['location_id']])
            ).values('category_id', 'text_general', 'text_anomaly')
            texts = read_frame(texts)

        return scores, texts, reference_start_location
    
    return scores, reference_start_location


def clean_previous_locations(previous_locations: list[str], locations: pd.DataFrame = None):
    """
    Split the previous locations into locations and countries.
    If the location is a country, return all locations in that country.
    """
    if locations is None:
        locations = read_frame(
            CoreLocations.objects.values('location_id', 'country', 'country_code')
        ).set_index('location_id')
    
    selected_locations = []
    selected_countries = {}
    for location in previous_locations:
        try:
            selected_locations.append(int(location))
        except:
            locations_country = locations.loc[locations.country_code == location, :]
            selected_countries[locations_country.country.iloc[0]] = locations_country.index.tolist()
    return selected_locations, selected_countries


class HomeView(TemplateView):
    template_name = 'home.html'

class DiscoverView(FormView):
    template_name = 'discover.html'
    form_class = TravellersInputForm
    success_url = '/list'

    def get_initial(self):
        initial = super().get_initial()
        initial.update(self.request.session.get('travellers_input_form_data', {}))
        return initial

    def form_valid(self, form):
        self.form_data = form.cleaned_data
        return super().form_valid(form)

    def get_success_url(self):
        url = reverse('locations_list')
        query_string = encode_url_parameters(self.form_data)
        url = f"{url}?{query_string}"
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['travellers_input_form'] = context.pop('form')
        context['grouped_locations'] = get_locations_for_select2()
        context['preselected_previous_locations'] = (
            self.request.session
            .get('travellers_input_form_data', {})
            .get('previous_locations', [])
        )
        return context


class SearchView(FormView):
    template_name = 'search.html'
    form_class = SearchLocationForm

    def get_initial(self):
        initial = super().get_initial()
        travellers_input_form_data = self.request.session.get('travellers_input_form_data', {})
        initial.update(travellers_input_form_data)
        return initial

    def form_valid(self, form):
        form_data = form.cleaned_data
        travellers_input_form_data = self.request.session.get('travellers_input_form_data', {})

        # Delete empty fields from form data
        fields = {
            'start_date': ['start_date', 'end_date'],
            'start_location': ['start_location', 'start_location_lat', 'start_location_lon']
        }
        for test_field, related_fields in fields.items():
            if form_data[test_field] == '':
                for field in related_fields:
                    del form_data[field]

        travellers_input_form_data.update(form_data)
        self.request.session['travellers_input_form_data'] = travellers_input_form_data
        
        location_id = form_data.pop('location')
        url = reverse('location_detail', args=[location_id])
        params = encode_url_parameters(form_data)
        url_with_params = f'{url}?{params}' if len(params) > 0 else url
        return HttpResponseRedirect(url_with_params)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_location_form'] = context.pop('form')
        context['grouped_locations'] = get_locations_for_select2()
        context['searched_location'] = self.request.session.get('travellers_input_form_data', {}).get('location', [])
        return context


class CompareView(View):
    template_name = 'compare.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)
    
    def get_context_data(self, **kwargs):

        # Get location ids
        location_ids = [
            int(location_id) for location_id in self.request.GET.getlist('locations')
        ]

        # Get locations
        locations = read_frame(
            CoreLocations.objects
            .filter(location_id__in=location_ids)
            .values('location_id', 'city', 'country', 'country_code')
        )

        # Get scores
        scores, reference_start_location = get_scores(
            start_date=self.request.GET.get('start_date'),
            end_date=self.request.GET.get('end_date'),
            start_location_lat=self.request.GET.get('start_location_lat'),
            start_location_lon=self.request.GET.get('start_location_lon'),
            location_id=location_ids,
            retrieve_text=False
        )

        context = {
            'locations': locations.to_dict('records'),
            'scores': scores.to_dict('records'),
        }

        return context


class AboutView(TemplateView):
    template_name = 'about.html'


class LocationsListView(View):
    template_name = 'list.html'

    def get(self, request, *args, **kwargs):

        # Form instance
        self.travellers_input_form = TravellersInputForm(self.request.GET)
        self.filters_form = FiltersForm(self.request.GET)
        self.preferences_form = PreferencesForm(self.request.GET)

        def compare_form_with_session(form, session_key, check_validity=True):
            """Compare form with session data."""
            session_data = self.request.session.get(session_key, {})
            valid = form.is_valid() # Call such that clean_data is available
            if check_validity:
                if valid:
                    form_data = form.cleaned_data
                else:
                    raise ValueError('Form is not valid.')
            else:
                form_data = form.clean()
            if form_data != session_data:
                self.request.session[session_key] = form_data
                return True
            return False
        
        # Check if forms changed compared to session (will update session)
        # Using two separate staements to call both functions
        # Otherwise if first is True, second will not be called
        ti_form_changed = compare_form_with_session(
            self.travellers_input_form, 'travellers_input_form_data'
        )
        preferences_form_changed = compare_form_with_session(
            self.preferences_form, 'preferences_form_data', check_validity=False
        )
        forms_changed = ti_form_changed or preferences_form_changed

        # If location list not in session or parameters changed
        if 'locations_list' not in self.request.session or forms_changed:
            self.locations_list = self.get_locations_list()
            self.request.session['locations_list'] = self.locations_list.to_dict(orient='list')
        # Otherwise get location list from session
        else:
            self.locations_list = pd.DataFrame(self.request.session['locations_list'])

        # Filter locations
        if compare_form_with_session(self.filters_form, 'filters_form_data'):
            self.filter_locations()
        
        # Sort locations based on the sort parameter
        self.sort_param = self.request.GET.get('sort', 'relevance_desc')
        sort_options = {
            'relevance_desc': ('relevance', False),
            'distance_asc': ('distance_to_start', True),
            'distance_desc': ('distance_to_start', False),
            'name_asc': ('city', True),
            'name_desc': ('city', False),
        }
        sort_column, sort_order = sort_options.get(self.sort_param)
        self.locations_list = self.locations_list.sort_values(
            by=sort_column, ascending=sort_order, ignore_index=True
        )

        # Convert to object_list (add rank)
        object_list = (
            self.locations_list
            .reset_index().rename(columns={'index': 'rank'})
            .assign(rank=lambda x: x['rank'] + 1)
            .to_dict('records')
        )

        # Create Paginator and get page
        self.page = Paginator(
            object_list=object_list,
            per_page=36
        ).get_page(self.request.GET.get('page'))

        # Assemble context
        context = self.get_context_data()

        return render(request, self.template_name, context)

    def get_locations_list(self):
        """Get list of locations and their respective relevance scores."""

        # Get parameters from travellers input form
        ti_form_data = self.request.session.get('travellers_input_form_data', {})

        # Get locations
        cols = [
            'location_id','city', 'country', 'country_code', 'lat', 'lon',
            'population'
        ]
        locations = read_frame(CoreLocations.objects.values(*cols))
        locations.set_index('location_id', inplace=True)

        # Get previous locations
        previous_locations = ti_form_data['previous_locations']
        previous_locations, previous_countries = clean_previous_locations(
            previous_locations, locations
        )

        # Store population histogram data
        self.request.session['population_hist_data'] = create_hist_for_slider(locations['population'])

        # Compute distance to start location
        locations['distance_to_start'] = haversine(
            lon1=ti_form_data['start_location_lon'],
            lat1=ti_form_data['start_location_lat'],
            lon2=locations['lon'].astype(float), #FIXME dtype
            lat2=locations['lat'].astype(float) #FIXME dtype
        )
        locations = locations.loc[locations['distance_to_start'] > 1] # Only locations further than 1 km
        self.request.session['distance_to_start_hist_data'] = create_hist_for_slider(locations['distance_to_start'])

        # Get scores
        scores, reference_start_location = get_scores(
            start_date=ti_form_data['start_date'],
            end_date=ti_form_data['end_date'],
            start_location_lat=ti_form_data['start_location_lat'],
            start_location_lon=ti_form_data['start_location_lon']
        )

        # Extract raw_values (for filters, only for a few dimensions), to do so:

        # Store raw values format in session
        relevant_dimensions = [21, 22, 41, 42, 61, 62, 63]
        raw_values_format = read_frame(
            CoreDimensions.objects
            .filter(dimension_id__in=relevant_dimensions)
            .values('dimension_id', 'raw_value_decimals', 'raw_value_unit')
        ).set_index('dimension_id')
        mapping = {
            21: 'temperature',
            41: 'travel',
            42: 'accommodation',
            61: 'best_reachability'
        }
        self.request.session['raw_values_format'] = (
            raw_values_format
            .assign(dimension = lambda x: x.index.map(mapping))
            .dropna()
            .reset_index(drop=True)
            .set_index('dimension')
            .to_dict('index')
        )

        # Pivot raw values
        raw_values = (
            scores
            .assign(dimension_id=clean_id(scores['dimension_id']))
            .query('dimension_id in @relevant_dimensions')
            .pivot(columns='dimension_id', index='location_id', values='raw_value')
            .query('index not in @previous_locations')
        )

        # Add possibly missing columns + round raw values
        for dimension_id in relevant_dimensions:
            if dimension_id not in raw_values.columns:
                raw_values[dimension_id] = np.nan
            else:
                raw_values[dimension_id] = (
                    raw_values[dimension_id]
                    .round(int(raw_values_format.loc[dimension_id, 'raw_value_decimals']))
                )
        raw_values.rename(columns=lambda x: 'dim_' + str(x), inplace=True)
        
        # Add column for best reachability
        raw_values['best_reachability'] = raw_values[['dim_61', 'dim_62', 'dim_63']].min(axis=1)

        # Add to locations (joined by pandas index)
        locations = locations.join(raw_values.astype(float), how='left')

        # Create histogram data for raw values
        self.request.session[f'travel_cost_hist_data'] = create_hist_for_slider(locations['dim_41'])
        self.request.session[f'accommodation_cost_hist_data'] = create_hist_for_slider(locations['dim_42'])
        self.request.session[f'best_reachability_hist_data'] = create_hist_for_slider(locations['best_reachability'])

        # Store temperature range limits
        temperature = raw_values[['dim_21', 'dim_22']].values
        self.request.session['temperature_range_limits'] = {
            'min': temperature.min(),
            'max': temperature.max()
        }

        # Add distance_to_start (as score scaled to [0,1])
        distance_to_start_scores = (
            (locations['distance_to_start']/locations['distance_to_start'].max())
            .reset_index()
            .assign(category_id=999, dimension_id=9999)
            .rename(columns={'distance_to_start': 'score'})
        )
        scores = pd.concat([scores, distance_to_start_scores])

        # Compute relevance score and add to DataFrame
        # (correctly joined by pandas index)
        locations['relevance'] = compute_relevance(
            previous_locations=previous_locations,
            previous_countries=previous_countries,
            scores=scores,
            preferences=self.request.session.get('preferences_form_data')
        )

        # Separate previous locations
        self.request.session['previous_locations_list'] = (
            locations
            .loc[previous_locations, :]
            .reset_index()
            .to_dict('records')
        )
        locations = locations.drop(previous_locations)

        return locations.reset_index()
    
    def filter_locations(self):
        """Filter locations based on user input."""

        # Get form data
        filters_form_data = self.request.session['filters_form_data']

        # Distance to start location
        min_distance = filters_form_data['min_distance']
        max_distance = filters_form_data['max_distance']
        if min_distance is not None and max_distance is not None:
            self.locations_list = self.locations_list[
                (self.locations_list['distance_to_start'] >= min_distance)
                & (self.locations_list['distance_to_start'] <= max_distance)
            ]

        # Population
        min_population = filters_form_data['min_population']
        max_population = filters_form_data['max_population']
        if min_population is not None and max_population is not None:
            self.locations_list = self.locations_list[
                (self.locations_list['population'] >= min_population)
                & (self.locations_list['population'] <= max_population)
            ]

        # Temperature
        min_temperature = filters_form_data['min_temperature']
        max_temperature = filters_form_data['max_temperature']
        if min_temperature is not None and max_temperature is not None:
            self.locations_list = self.locations_list[
                (self.locations_list['dim_22'] >= min_temperature)
                & (self.locations_list['dim_21'] <= max_temperature)
            ]

        # Simple raw value filters
        raw_value_filters = {
            'min': {
                'travel_cost': 'dim_41',
                'accommodation_cost': 'dim_42',
                'best_reachability': 'best_reachability'
            },
            'max': {
                'travel_cost': 'dim_41',
                'accommodation_cost': 'dim_42',
                'best_reachability': 'best_reachability'
            }
        }
        for filter_name, dimension in raw_value_filters['min'].items():
            value = filters_form_data.get(f'min_{filter_name}')
            if value is not None:
                self.locations_list = self.locations_list[
                    self.locations_list[dimension] >= value
                ]
        for filter_name, dimension in raw_value_filters['max'].items():
            value = filters_form_data.get(f'max_{filter_name}')
            if value is not None:
                self.locations_list = self.locations_list[
                    self.locations_list[dimension] <= value
                ]
    
    def get_context_data(self, **kwargs):
        """Assemble context for template."""

        # Assemble query params from GET request for LocationDetailView
        query_parameters = encode_url_parameters(self.request.session['travellers_input_form_data'])

        context = {
            'locations_list': self.page,
            'previous_locations_list': self.request.session['previous_locations_list'],
            'current_sort_order': self.sort_param,
            'travellers_input_form': self.travellers_input_form,
            'filters_form': self.filters_form,
            'preferences_form': self.preferences_form,
            'distance_to_start_hist_data': self.request.session['distance_to_start_hist_data'],
            'population_hist_data': self.request.session['population_hist_data'],
            'travel_cost_hist_data': self.request.session['travel_cost_hist_data'],
            'accommodation_cost_hist_data': self.request.session['accommodation_cost_hist_data'],
            'best_reachability_hist_data': self.request.session['best_reachability_hist_data'],
            'temperature_range_limits': self.request.session['temperature_range_limits'],
            'raw_values_format': self.request.session['raw_values_format'],
            'query_parameters': query_parameters,
            'comparison_params': get_comparison_params(self.request.session),
            'grouped_locations': get_locations_for_select2(),
            'preselected_previous_locations': self.request.session['travellers_input_form_data']['previous_locations']
        }

        return context


class LocationDetailView(DetailView):
    model = CoreLocations
    template_name = 'location_detail.html'
    pk_url_kwarg = 'location_id'
    context_object_name = 'location'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get location
        location = get_object_or_404(CoreLocations, pk=self.kwargs['location_id'])

        # Get image
        image = read_frame(
            CoreLocationsImages.objects
            .filter(location_id=location.location_id)
            .values('img_url')
        ).img_url.item()

        # Get scores and texts
        scores, texts, reference_start_location = get_scores(
            start_date=self.request.GET.get('start_date'),
            end_date=self.request.GET.get('end_date'),
            start_location_lat=self.request.GET.get('start_location_lat'),
            start_location_lon=self.request.GET.get('start_location_lon'),
            location_id=location.location_id,
            retrieve_text=True
        )
        scores = (
            scores
            .filter(['dimension_id', 'score', 'raw_value'])
            .assign(dimension_id=clean_id(scores.dimension_id))
            .set_index('dimension_id')
        )
        texts = (
            texts
            .assign(category_id=clean_id(texts.category_id))
            .set_index('category_id')
        )

        # Get categories with related dimensions
        categories_with_dimensions = CoreCategories.objects.prefetch_related(
            Prefetch('coredimensions_set')
        )

        def format_raw_value(dimension: int) -> str:
            """Format raw value."""
            if dimension.dimension_id not in scores.index:
                return None
            if pd.isna(scores.loc[dimension.dimension_id, 'raw_value']):
                return ''
            raw_value = scores.loc[dimension.dimension_id, 'raw_value']
            return f' ({raw_value:.{dimension.raw_value_decimals}f}{dimension.raw_value_unit})'
        
        # Convert to list of dictionaries, with dimensions and scores
        data = [
            {
                'category_id': category.category_id,
                'category_name': category.category_name,
                'category_description': category.description,
                'display_order': category.display_order,
                'axis_title': category.axis_title,
                'axis_label_low': category.axis_label_low,
                'axis_label_high': category.axis_label_high,
                'text_general': texts.loc[category.category_id, 'text_general'] if category.category_id in texts.index else None,
                'text_anomaly': texts.loc[category.category_id, 'text_anomaly'] if category.category_id in texts.index else None,
                'dimensions': [
                    {
                        'dimension_id': dimension.dimension_id,
                        'dimension_name': dimension.dimension_name,
                        'dimension_description': dimension.description,
                        'dimension_icon_url': dimension.icon_url,
                        'score': scores.loc[dimension.dimension_id, 'score'].item() if dimension.dimension_id in scores.index else None,
                        'raw_value_formatted': format_raw_value(dimension),
                    }
                    for dimension in category.coredimensions_set.all()
                ],
            }
            for category in categories_with_dimensions
        ]

        # Order by display_order
        data = sorted(data, key=lambda x: x['display_order'])

        # Get weather data
        weather_fields = ['year', 'month', 'temperature_max', 'temperature_min', 'precipitation_sum']
        weather_dtypes = {
            'temperature_max': float,
            'temperature_min': float,
            'precipitation_sum': float
        }
        weather_data = read_frame(
            RawWeatherHistorical.objects
            .filter(location_id=location.location_id)
            .values(*weather_fields)
        )
        weather_data = (
            weather_data
            .astype(weather_dtypes)
            .groupby('month')
            .agg({
                'year': ['min', 'max'],
                'temperature_max': 'mean',
                'temperature_min':
                'mean', 'precipitation_sum': 'mean'
            })
            .reset_index()
            .sort_values('month')
        )
        weather_data.columns = [
            '_'.join(col).strip() if col[0] == 'year' else col[0]
            for col in weather_data.columns.values
        ]
        months = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 
            6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 
            11: 'Nov', 12: 'Dec'
        }
        weather_data['month'] = weather_data['month'].map(months)
        weather_data_years = {
            col: weather_data.pop(col).iloc[0] for col in ['year_min', 'year_max']
        }
        weather_data = weather_data.to_dict('records')

        # Get travel warnings
        travel_warning = (
            RawTravelWarnings
            .objects
            .filter(country_code=location.country_code)
            .values('warning_text', 'link')
            .first()
        )
        if travel_warning:
            context['travel_warning'] = travel_warning

        # Get money text
        money_text = (
            RawCurrencyTexts
            .objects
            .filter(location_id=location.location_id)
            .values('text')
            .first()
        )
        if money_text:
            context['money_text'] = money_text['text']

        # Get top attractions
        top_attractions = list(
            RawCultureSights
            .objects
            .filter(location_id=location.location_id)
            .order_by('sight_rank')
            .values_list('sight', flat=True)
        )
        if len(top_attractions) > 0:
            context['top_attractions'] = top_attractions

        # Get reference start location airport
        reference_start_airport = (
            CoreAirports.objects
            .values('iata_code', 'airport_name', 'city')
            .filter(iata_code=reference_start_location['mapped_start_airport'].strip()) #FIXME no FK + strip needed
            .first()
        )

        # Get previous locations
        previous_locations, previous_countries = clean_previous_locations(
            self.request.GET.getlist('previous_locations', [])
        )
        if len(previous_locations) > 0:
            previous_locations = (
                CoreLocations
                .objects
                .filter(location_id__in=previous_locations)
                .values('location_id', 'city', 'country')
            )
            context['previous_locations'] = previous_locations
            context['previous_countries'] = previous_countries
            
        # Add to context
        context.update({
            'start_location': self.request.GET.get('start_location'),
            'reference_start_location': reference_start_location,
            'reference_start_airport': reference_start_airport,
            'image': image,
            'location': location,
            'data': data,
            'weather_data': weather_data,
            'weather_data_years': weather_data_years,
            'comparison_params': get_comparison_params(self.request.session),
        })

        return context

