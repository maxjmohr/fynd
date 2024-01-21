from django.views import View
from django.views.generic import TemplateView, ListView, FormView
from django.views.generic.detail import DetailView
from django.views.generic.edit import ModelFormMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.core.paginator import Paginator
from django import forms
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import render, redirect
from django.db.models import Q
from .models import (
    CoreScores,
    CoreLocations,
    CoreLocationsImages,
    CoreDimensions,
    CoreCategories,
)
from .forms import *
from .compute_relevance import compute_relevance
from .compute_haversine import haversine
import numpy as np
import pandas as pd
from urllib.parse import urlencode
from django_pandas.io import read_frame

import time


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


def create_hist_for_slider(data: pd.Series, bins:  int = 30):
    hist, bin_edges = np.histogram(data, bins=30)
    return {'heights': hist.tolist(), 'binLimits': bin_edges.tolist()}


def get_scores(
        start_date: str,
        end_date: str,
        start_location_lat: str,
        start_location_lon: str,
        location_id: int = None):
    
    # Convert start and end date to datatime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Convert start location to float
    start_location_lat = float(start_location_lat)
    start_location_lon = float(start_location_lon)
    
    # Get closest reference location for start location -----------------------
    #FIXME

    start_location_proxy = 'palceholder'


    # Get filtered scores -----------------------------------------------------

    # Filter
    query = CoreScores.objects.filter(
        Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
    )

    if location_id is not None:
        query = query.filter(location_id__in=location_id)

    # Define fileds to include in values() (negative selection)
    all_fields = [f.name for f in CoreScores._meta.get_fields()]
    exclude_fields = ['updated_at']
    include_fields = [f for f in all_fields if f not in exclude_fields]

    # Get as DataFrame
    scores = read_frame(query.values(*include_fields)).astype({'score': float})

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
    scores['score'] *= scores['overlap_days']
    scores = (
        scores
        .groupby(['location_id', 'category_id', 'dimension_id'])
        .agg({'score': 'sum', 'overlap_days': 'sum'})
    )
    scores['score'] /= scores['overlap_days']
    scores.drop(columns=['overlap_days'], inplace=True)
    scores.reset_index(inplace=True)

    return scores, start_location_proxy


class HomeView(TemplateView):
    template_name = 'home.html'

class DiscoverView(FormView):
    template_name = 'discover.html'
    form_class = TravellersInputForm
    success_url = '/list'

    def form_valid(self, form):
        form_data = {
            'previous_locations': list(
                form.cleaned_data['previous_locations']
                .values_list('location_id', flat=True)
            ),
            'start_date': form.cleaned_data['start_date'],
            'end_date': form.cleaned_data['end_date'],
            'start_location': form.cleaned_data['start_location'],
            'start_location_lat': form.cleaned_data['start_location_lat'],
            'start_location_lon': form.cleaned_data['start_location_lon'],
        }
        self.request.session.update(form_data)

        return super().form_valid(form)

    def get_success_url(self):
        data = {
            'start_date': self.request.session['start_date'],
            'end_date': self.request.session['end_date'],
            'start_location': self.request.session['start_location'],
            'start_location_lon': self.request.session['start_location_lon'],
            'start_location_lat': self.request.session['start_location_lat'],
            'previous_locations': self.request.session['previous_locations']
        }
        url = reverse('locations_list')
        query_string = encode_url_parameters(data)
        url = f"{url}?{query_string}"
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['travellers_input_form'] = context.pop('form')
        return context


class SearchView(FormView):
    template_name = 'search.html'
    form_class = SearchLocationForm

    def form_valid(self, form):
        location = form.cleaned_data['location']
        self.request.session['searched_location'] = location.location_id
        return HttpResponseRedirect(reverse('location_detail', args=[location.location_id]))


class CompareView(TemplateView):
    template_name = 'compare.html'


class AboutView(TemplateView):
    template_name = 'about.html'


class LocationsListView(View):
    template_name = 'list.html'

    def get(self, request, *args, **kwargs):

        # Form instance
        self.travellers_input_form = TravellersInputForm(self.request.GET)
        self.filters_form = FiltersForm(self.request.GET)

        # Get parameters from the request
        self.params = self.request.GET.dict()
        if 'sort' in self.params:
            del self.params['sort']

        # Merge the new parameters with the existing ones
        new_params = QueryDict('', mutable=True)
        new_params.update(self.params)

        # Check if the queryset is in the session
        # and if GET parameters have changed (apart form sorting)
        # If yes, (re)compute the queryset and store it in the session
        first_run = 'location_list' not in self.request.session
        params_changed = self.params != self.request.session.get('params', {})
        if first_run or params_changed:
            location_list = self.get_queryset()
            self.request.session['location_list'] = location_list.to_dict(orient='list')
            self.request.session['params'] = self.params
        else:
            location_list = pd.DataFrame(self.request.session['location_list'])
        
        # Sort the queryset based on the sort parameter
        self.sort_param = self.request.GET.get('sort', 'relevance_desc')
        sort_options = {
            'relevance_desc': ('relevance', False),
            'distance_asc': ('distance_to_start', True),
            'distance_desc': ('distance_to_start', False),
            'name_asc': ('city', True),
            'name_desc': ('city', False),
        }
        sort_column, sort_order = sort_options.get(self.sort_param)
        location_list = location_list.sort_values(
            by=sort_column, ascending=sort_order
        )
        
        # Create a Paginator
        self.paginator = Paginator(
            object_list=location_list.reset_index().to_dict('records'),
            per_page=50
        )

        # Get the page number from the GET parameters
        page_number = self.request.GET.get('page')

        # Get the page of objects
        self.page = self.paginator.get_page(page_number)

        # Render the template with the context data
        context = self.get_context_data()

        return render(request, self.template_name, context)

    def get_queryset(self):

        # GET LOCATIONS -------------------------------------------------------
        cols = ['location_id', 'city', 'country', 'country_code', 'lat', 'lon']
        locations = read_frame(CoreLocations.objects.values(*cols))
        locations.set_index('location_id', inplace=True)

        # DISTANCE TO START LOCATION ------------------------------------------

        start_location_lat = self.params.get('start_location_lat')
        start_location_lon = self.params.get('start_location_lon')
        locations['distance_to_start'] = haversine(
            lon1=float(start_location_lon),
            lat1=float(start_location_lat),
            lon2=locations['lon'].astype(float), #FIXME dtype
            lat2=locations['lat'].astype(float) #FIXME dtype
        )
        self.request.session['distance_to_start_hist_data'] = create_hist_for_slider(locations['distance_to_start'])
        
        # FILTER --------------------------------------------------------------

        # Get the distance range from the session #FIXME get from GET request
        min_distance = self.params.get('min_distance', None)
        max_distance = self.params.get('max_distance', None)

        # If a distance range is set, filter the DataFrame
        if min_distance is not None and max_distance is not None:
            locations = locations[
                (locations['distance_to_start'] >= float(min_distance))
                & (locations['distance_to_start'] <= float(max_distance))
            ]

        # RELEVANCE SCORES ----------------------------------------------------

        # Previous locations user input
        previous_locations = self.request.GET.getlist('previous_locations')
        previous_locations = [int(loc_id) for loc_id in previous_locations]

        # Get scores
        scores, start_location_proxy = get_scores(
            start_date=self.params.get('start_date'),
            end_date=self.params.get('end_date'),
            start_location_lat=self.params.get('start_location_lat'),
            start_location_lon=self.params.get('start_location_lon'),
            location_id=locations.index.tolist() + previous_locations
        )

        # Rescale scores based on number of dimensions per category
        n_dims_per_category = (
            read_frame(CoreDimensions.objects.values('category_id'))
            .category_id
            .value_counts()
            .rename('n_dims')
        )
        # Reverse such that scores of categories with more dimensions get lower weights
        weights = 1/n_dims_per_category
        weights.rename('weight', inplace=True)

        # Incorporate user preferences
        user_preferences = {
            'CoreCategories object (1)': 0.88,
            'CoreCategories object (2)': 0.34,
            'CoreCategories object (3)': 0.12,
            'CoreCategories object (4)': 0.55,
            'CoreCategories object (5)': 0.66,
            'CoreCategories object (6)': 0.77,
            'CoreCategories object (7)': 0.89,
            'distance_to_start': 1.89,
        }
        #user_preferences = None #FIXME
        if user_preferences:
            # Convert user preferences to pandas Series
            user_preferences_series = pd.Series(user_preferences, name='weight')
            user_preferences_series.index.name = 'category_id'

            # Multiply with weights from number of dimensions per category
            # Categories are matched by index of pandas Series
            weights = weights * user_preferences_series

        # Multiply scores with weights
        scores = scores.merge(weights, on='category_id', how='left')
        scores['score'] *= scores['weight']
        scores.drop(columns=['weight'], inplace=True)

        # Pivot scores (from long to wide)
        scores = (
            scores
            .pivot(index='location_id', columns='dimension_id', values='score')
            .rename_axis(None, axis=1)
        )

        # Add distance_to_start to scores
        # (scaled to [0,1] and multiplied with user preference)
        distance_to_start_score = (
            locations['distance_to_start']/locations['distance_to_start'].max()
        )
        if user_preferences:
            distance_to_start_score *= user_preferences['distance_to_start'] #FIXME
        scores['distance_to_start'] = distance_to_start_score

        #FIXME Replace missings
        scores.fillna(-1, inplace=True)

        # Compute relevance score and add to DataFrame
        # (correctly joined by pandas index)
        locations['relevance'] = compute_relevance(
            previous_locations=previous_locations,
            scores=scores
        )

        # THUMBNAILS ----------------------------------------------------------
        thumbnails = read_frame(
            CoreLocationsImages.objects.values('location_id', 'img_url')
        )
        thumbnails.set_index('location_id', inplace=True)
        locations['thumbnail_url'] = thumbnails['img_url']

        # ---------------------------------------------------------------------
        
        return locations.reset_index()
    
    def get_context_data(self, **kwargs):
        context = {
            'location_list': self.page,
            'current_sort_order': self.sort_param,
            'travellers_input_form': self.travellers_input_form,
            'filters_form': self.filters_form,
            'distance_to_start_hist_data': self.request.session['distance_to_start_hist_data'],
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

        # Add scores to context
        if False:
            scores, start_location_proxy = get_scores(
                start_date=self.request.session['start_date'],
                end_date=self.request.session['end_date'],
                start_location_lat=self.request.session['start_location_lat'],
                start_location_lon=self.request.session['start_location_lon'],
                location_id=[location.location_id]
            )

        # Add thumbnails to context
        image = read_frame(
            CoreLocationsImages.objects
            .filter(location_id=location.location_id)
            .values('img_url')
        ).img_url.item()

        print(image)

        categories = read_frame(CoreCategories.objects.all()).to_dict('records')
        print(categories)

        context.update({
            #'start_location_proxy': start_location_proxy,
            #'scores': scores,
            'image': image,
            'location': location,
            'categories': categories,
        })

        # Add any additional data to the context here. For example:
        # context['graph_data'] = self.get_graph_data(location)

        return context

