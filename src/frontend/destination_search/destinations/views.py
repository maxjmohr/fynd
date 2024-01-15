from django.views import View
from django.views.generic import TemplateView, ListView, FormView
from django.views.generic.detail import DetailView
from django.views.generic.edit import ModelFormMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.core.paginator import Paginator
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from .models import CoreScores, CoreLocations, CoreLocationsImages
from .filters import LocationsFilterset
from .forms import *
from .compute_relevance import compute_relevance
from .compute_haversine import haversine
import numpy as np
import pandas as pd
from urllib.parse import urlencode
from django_pandas.io import read_frame


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


class HomeView(TemplateView):
    template_name = 'home.html'

class DiscoverView(FormView):
    template_name = 'discover.html'
    form_class = TravellersInputForm
    success_url = '/list'

    def form_valid(self, form):
        self.request.session['previous_locations'] = list(
            form.cleaned_data['previous_locations']
            .values_list('location_id', flat=True)
        )
        start_date, end_date = form.cleaned_data.get('date_range')
        self.request.session['start_date'] = start_date
        self.request.session['end_date'] = end_date
        self.request.session['start_location'] = form.cleaned_data['start_location']
        self.request.session['start_location_lat'] = form.cleaned_data['start_location_lat']
        self.request.session['start_location_lon'] = form.cleaned_data['start_location_lon']
        return super().form_valid(form)

    def get_success_url(self):
        data = {
            'start_date': self.request.session['start_date'],
            'end_date': self.request.session['end_date'],
            'start_location_lon': self.request.session['start_location_lon'],
            'start_location_lat': self.request.session['start_location_lat'],
            'previous_locations': self.request.session['previous_locations']
        }
        url = reverse('locations_list')
        query_string = encode_url_parameters(data)
        url = f"{url}?{query_string}"
        return url


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

        # Get parameters from the request
        self.params = self.request.GET.dict()

        # Get sorting parameter
        self.sort_param = self.request.GET.get('sort', 'relevance_desc')

        # Perform calculations and get queryset
        object_list = self.get_queryset()

        # Create a Paginator
        self.paginator = Paginator(
            object_list=object_list,
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

        #FIXME
        start_location_lat = self.params.get('start_location_lat')
        start_location_lon = self.params.get('start_location_lon')
        locations['distance_to_start'] = haversine(
            lon1=float(start_location_lon),
            lat1=float(start_location_lat),
            lon2=locations['lon'].astype(float), #FIXME dtype
            lat2=locations['lat'].astype(float) #FIXME dtype
        )
        
        # FILTER --------------------------------------------------------------

        # Get the distance range from the session #FIXME get from GET request
        min_distance = self.request.session.get('min_distance', None)
        max_distance = self.request.session.get('max_distance', None)

        # If a distance range is set, filter the DataFrame
        if min_distance is not None and max_distance is not None:
            locations = locations[(locations['distance_to_start'] >= min_distance) & (locations['distance_to_start'] <= max_distance)]

        # RELEVANCE SCORES ----------------------------------------------------

        # Get dates of travel
        start_date = self.params.get('start_date')
        end_date = self.params.get('end_date')

        # Fetch score data, convert to DataFrame and pivot
        scores = (
            read_frame(CoreScores.objects.values('location_id', 'dimension_id', 'score'))
            .pivot(index='location_id', columns='dimension_id', values='score')
            .rename_axis(None, axis=1)
        )

        #FIXME filter for valid dates based on start_date and end_date

        # Add distance_to_start to scores
        scores['distance_to_start'] = locations['distance_to_start']  #FIXME check if correctly joined

        #FIXME
        scores.fillna(-1, inplace=True)
            
        # Previous locations user input
        previous_locations = self.request.GET.getlist('previous_locations')
        previous_locations = [int(loc_id) for loc_id in previous_locations]

        # Compute relevance score and add to DataFrame (correctly joined by pandas index)
        locations['relevance'] = compute_relevance(
            previous_locations=previous_locations,
            scores=scores
        )

        # SORT ----------------------------------------------------------------

        # Sort locations based on sort parameter
        sort_options = {
            'relevance_desc': ('relevance', False),
            'distance_asc': ('distance_to_start', True),
            'distance_desc': ('distance_to_start', False),
            'name_asc': ('city', True),
            'name_desc': ('city', False),
        }
        sort_column, sort_order = sort_options.get(self.sort_param)
        locations = locations.sort_values(by=sort_column, ascending=sort_order)

        # THUMBNAILS ----------------------------------------------------------
        thumbnails = read_frame(CoreLocationsImages.objects.values('location_id', 'img_url'))
        thumbnails.set_index('location_id', inplace=True)
        locations['thumbnail_url'] = thumbnails['img_url']

        # ---------------------------------------------------------------------

        # Convert DataFrame back to list of dictionaries
        return locations.reset_index().to_dict('records')
    
    def get_context_data(self, **kwargs):
        context = {
            'location_list': self.page,
            'current_sort_order': self.sort_param,
        }
        return context


class LocationDetailView(DetailView):
    model = CoreLocations
    template_name = 'location_detail.html'
    pk_url_kwarg = 'location_id'
    context_object_name = 'location'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        location = get_object_or_404(CoreLocations, pk=self.kwargs['location_id'])

        # Add any additional data to the context here. For example:
        # context['graph_data'] = self.get_graph_data(location)

        return context

