from django.core.exceptions import ImproperlyConfigured
from django.views.generic import ListView
from django_filters.filterset import FilterSet

"""
Example:

# View
class Posts(ModelResource):
    model = Post
    class List(ModelResource.List):
        class Search:
            content = filters.CharFilter(lookup_type='contains')
            order_by = [ 'title', 'content' ]


# Template
{% include '_form.html' with form=search.form method='get' %}

"""

class ListSearchMixin(object):
    """
    Mixin that adds support for django-filter
    """

    search_set = {}
    
    def get_search_set(self):
        if not isinstance(self.search_set, FilterSet):
            filter_dict = getattr(self, 'Search', self.search_set)
            if not isinstance(filter_dict, dict):
                filter_dict = filter_dict.__dict__.copy()
            if 'model' not in filter_dict and self.model:
                filter_dict['model']=self.model
            if 'model' in filter_dict:
                meta_dict = {}
                for attr in [ 'model', 'fields', 'exclude', 'order_by', 'form' ]:
                    if filter_dict.has_key(attr):
                        meta_dict[attr] = filter_dict[attr]
                        del filter_dict[attr]
                filter_dict['Meta']=type('Meta', (object,), meta_dict)
                self.search_set = type('%sFilterSet' % self.model._meta.object_name, (FilterSet,),
                    filter_dict)
        if self.search_set:
            return self.search_set
        
        raise ImproperlyConfigured(
                "ListFilterMixin requires either a definition of "
                "'search_set' as an FilterSet subclass or as a dictionary,"
                "or a definition of 'model', "
                "or an implementation of 'get_filter()'")


    def get_search_set_kwargs(self):
        """
        Returns the keyword arguments for instanciating the filterset.
        """
        return {
            'data': self.request.GET,
            'queryset': self.get_base_queryset(),
        }

    def get_base_queryset(self):
        """
        We can decided to either alter the queryset before or after applying the
        FilterSet
        """
        return super(ListSearchMixin, self).get_queryset()

    def get_constructed_filter(self):
        # We need to store the instantiated FilterSet cause we use it in
        # get_queryset and in get_context_data
        if getattr(self, 'constructed_filter', None):
            return self.constructed_filter
        else:
            f = self.get_search_set()(**self.get_search_set_kwargs())
            self.constructed_filter = f
            return f

    def get_queryset(self):
        return self.get_constructed_filter().qs

    def get_context_data(self, **kwargs):
        kwargs.update({'filter': self.get_constructed_filter()})
        return super(ListSearchMixin, self).get_context_data(**kwargs)


class ListFilteredView(ListSearchMixin, ListView):
    """
    A list view that can be filtered by django-filter
    """