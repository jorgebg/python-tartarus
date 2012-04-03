from django.views.generic import ListView
from django_easyfilters import FilterSet
from django_easyfilters.filters import FILTER_DISPLAY
from tartarus.utils import capfirst

class ListFilteredMixin(object):
    """
    Mixin for generic class-based views (e.g. django.views.generic.ListView) that can be filtered
    """
    # Replace the default django.core filter by FilterSet
    filter_class = None

    def get_filter(self, queryset, params=None):
        # Pass the request object to the filter to keep the parameters in the url querystring ("?filter=2&old_param=...")
        if params == None:
            params = self.request.GET
            
        filter_class = self.filter_class
        filter_attributes = None
            
        if hasattr(self, 'Filter'):
            if isinstance(self.Filter, FilterSet):
                filter_class = self.Filter
            else:
                filter_attributes = dict((k,v) for k, v in self.Filter.__dict__.iteritems() if not k.startswith('__'))
                
        if not filter_attributes:
            filter_attributes = getattr(self, 'filter_by')
        
        if filter_attributes and not filter_class:
            filter_class = type('Filter', (self.filter_class or FilterSet,), filter_attributes)
        elif not filter_class:
            return None
            
        return filter_class(queryset, params)

    def filter_queryset(self, filter, queryset):
        filters = [self.get_filter_representation(filter, field) for field in filter.filters]
        queryset=filter.apply_filters(queryset)
        is_filtered = False
        for filter in filters:
            for choice in filter['choices']:
                if choice['link_type'] == 'remove':
                    is_filtered = True
                    break
        return filters, queryset, is_filtered

    def get_filter_representation(self, filter, field):
        field_obj = filter.model._meta.get_field(field.field)
        choices = filter.get_filter_choices(field.field)
        context = {}
        context['label'] = capfirst(field_obj.verbose_name)
        context['choices'] = [dict(label=c.label,
                               url=u'?' + c.params.urlencode() \
                                   if c.link_type != FILTER_DISPLAY else None,
                               link_type=c.link_type,
                               count=c.count)
                          for c in choices]
        return context

    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        context = {}
        queryset = kwargs.pop('object_list')

        filter = self.get_filter(queryset)
        if filter:
            filters, queryset, is_filtered = self.filter_queryset(filter, queryset)
            context.update({
                'filters': filters,
                'is_filtered': is_filtered,
                'has_filters': True,
                'object_list': queryset
            })
        else:
            context.update({
                'filters': None,
                'has_filters': False,
                'object_list': queryset
            })
        
        context.update(kwargs)
        context_object_name = self.get_context_object_name(queryset)
        if context_object_name is not None:
            context[context_object_name] = queryset
        return context

class ListFilteredView(ListFilteredMixin, ListView):
    """
    A list view that can be filtered
    """
