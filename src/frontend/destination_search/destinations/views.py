from django.views import View
from django.views.generic import TemplateView, ListView, FormView
from django.views.generic.detail import DetailView
from django.views.generic.edit import ModelFormMixin
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from .models import CoreScores, CoreLocations
from .filters import LocationsFilterset
from .forms import PreviousLocationsForm
from .compute_relevance import compute_relevance
import numpy as np
import pandas as pd
from django_pandas.io import read_frame


class HomePageView(FormView):
    template_name = 'home.html'
    form_class = PreviousLocationsForm
    success_url = '/list'

    def form_valid(self, form):
        location_ids = form.cleaned_data['locations'].values_list('location_id', flat=True)
        self.request.session['previous_locations'] = list(location_ids)
        return super().form_valid(form)
    
class HomePageView2(View):
    template_name = 'home3.html'
    def get(self, request, *args, **kwargs):
        previous_locations_form = PreviousLocationsForm()
        return render(request, 'home.html', {'form': previous_locations_form})

    def post(self, request, *args, **kwargs):
        previous_locations_form = PreviousLocationsForm(request.POST)
        if previous_locations_form.is_valid():
            # Save form data in session
            request.session['previous_locations'] = request.POST
            return redirect('locations_list')

class LocationsListView(View):
    template_name = 'list.html'
    paginate_by = 50

    def get(self, request, *args, **kwargs):
        # Handle form data
        previous_data = {
            'locations': request.session.get('previous_locations', None)
        }
        self.previous_locations_form = PreviousLocationsForm(previous_data if previous_data else None)

        # Perform calculations and get queryset
        self.object_list = self.get_queryset()

        # Get sorting parameter
        self.sort_param = self.request.GET.get('sort', 'relevance_desc')

        # Create a Paginator
        self.paginator = Paginator(self.object_list, self.paginate_by)

        # Get the page number from the GET parameters
        page_number = self.request.GET.get('page')

        # Get the page of objects
        self.page = self.paginator.get_page(page_number)

        # Render the template with the context data
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        self.object = None #FIXME why?
        self.previous_locations_form = PreviousLocationsForm(request.POST)

        if self.previous_locations_form.is_valid():
            # Save the data in the session
            self.object = self.previous_locations_form.save() #FIXME why?
            request.session['previous_locations'] = self.previous_locations_form.cleaned_data['locations'].values_list('location_id', flat=True)
            return redirect('locations_list')
        else:
            return self.get(request, *args, **kwargs)

    def get_queryset(self):

        # RELEVANCE SCORES ----------------------------------------------------

        # Fetch score data, convert to DataFrame and pivot
        scores = (
            read_frame(CoreScores.objects.values('location_id', 'dimension_id', 'score'))
            .pivot(index='location_id', columns='dimension_id', values='score')
            .rename_axis(None, axis=1)
        )

        #FIXME --------------------------------------
        # Convert scores to float
        scores = scores.astype(float)
        # Add some dummy dimensions
        np.random.seed(123)
        for dim in ['41', '23', '11', '12', '31']:
            scores[dim] = scores.iloc[:,0] * np.random.uniform(0, 0.1, len(scores))
        # --------------------------------------------
            
        # Previous locations user input
        previous_locations = self.request.session.get('previous_locations', [])

        # FIXME remove locations for which we don't have scores
        previous_locations = [i for i in previous_locations if i in scores.index]

        # Compute relevance score
        relevance = compute_relevance(
            previous_locations=previous_locations,
            scores=scores
        )

        # ---------------------------------------------------------------------

        # Get distance to user start location #FIXME replace with actual user input
        distance_to_start = relevance * np.random.uniform(0, 100, len(relevance))

        # ASSEMBLE DATA -------------------------------------------------------

        # Join locations with relevance and distance_to_start
        cols = ['location_id', 'city', 'country', 'country_code']
        locations = read_frame(CoreLocations.objects.values(*cols))
        locations = locations.set_index('location_id')
        locations['relevance'] = relevance
        locations['distance_to_start'] = distance_to_start

        # FILTER --------------------------------------------------------------

        # Get the distance range from the session
        min_distance = self.request.session.get('min_distance', None)
        max_distance = self.request.session.get('max_distance', None)

        # If a distance range is set, filter the DataFrame
        if min_distance is not None and max_distance is not None:
            locations = locations[(locations['distance_to_start'] >= min_distance) & (locations['distance_to_start'] <= max_distance)]

        # SORT ----------------------------------------------------------------
        
        # Get sorting parameter
        self.sort_param = self.request.GET.get('sort', 'relevance_desc')

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

        # ---------------------------------------------------------------------

        # Convert DataFrame back to list of dictionaries
        return locations.reset_index().to_dict('records')
    
    def get_context_data(self, **kwargs):
        context = {
            'object_list': self.page,
            'previous_locations_form': self.previous_locations_form,
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

