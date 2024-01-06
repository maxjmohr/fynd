from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.core.paginator import Paginator
from .models import CoreScores, CoreLocations
from .filters import LocationsFilterset
from .compute_relevance import compute_relevance
import numpy as np
import pandas as pd
from django_pandas.io import read_frame


class HomePageView(TemplateView):
    template_name = 'home.html'

class LocationsListView(ListView):
    template_name = 'list.html'
    paginate_by = 50

    def get(self, request, *args, **kwargs):
        self.user_input = request.GET  # get user input from request parameters
        self.sort_param = request.GET.get('sort', 'relevance_desc')  # get sort parameter from request
        return super().get(request, *args, **kwargs)

    def get_queryset(self):

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
            
        # User input #FIXME replace with actual user input from form
        previous_locations = [20560154, 61941371, 237395083]

        # Compute relevance score
        relevance = compute_relevance(
            previous_locations=previous_locations,
            scores=scores
        )

        # Get distance to user start location #FIXME replace with actual user input
        distance_to_start = relevance * np.random.uniform(0, 100, len(relevance))

        # Join locations with relevance and distance_to_start
        cols = ['location_id', 'city', 'country', 'country_code']
        locations = read_frame(CoreLocations.objects.values(*cols))
        locations = locations.set_index('location_id')
        locations['relevance'] = relevance
        locations['distance_to_start'] = distance_to_start

        # Sort locations based on sort parameter
        sort_options = {
            'relevance_desc': ('relevance', False),
            'distance_asc': ('distance_to_start', True),
            'distance_desc': ('distance_to_start', False),
            'name_asc': ('city', True),
            'name_desc': ('city', False),
        }
        sort_column, sort_order = sort_options.get(self.sort_param, ('relevance', False))
        locations = locations.sort_values(by=sort_column, ascending=sort_order)

        print(locations.columns)

        # Convert DataFrame back to list of dictionaries
        return locations.reset_index().to_dict('records')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Set current_sort_order in the context
        context['current_sort_order'] = self.sort_param

        # Create a Paginator
        paginator = Paginator(self.get_queryset(), self.paginate_by)

        # Get the page number from the GET parameters
        page_number = self.request.GET.get('page')

        # Get the page of objects
        page = paginator.get_page(page_number)

        # Update the context
        context.update({
            'object_list': page,
        })

        return context

