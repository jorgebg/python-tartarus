from tartarus.django.sort import Sort, Choice, InvalidChoice
from django.views.generic import ListView
from django.http import Http404
from django.utils.translation import ugettext as _

"""
Example:


    class List(ListView):
        order_by = {
            'title': ('title',),
            'newer_first': ('date', {'label': 'Date: New to old'}),
            'older_first': ('-date', {'label': 'Date: Old to new'}),
            'length': ('length', {'extra':{'select':{'length':'Length(content)'}}})
        }
        class Sort:
            title = Choice('title')
            content_and_title = Choice('title', 'content')
            newer_first = Choice('date', label='Date: New to old')
            older_first = Choice('-date', label='Date: Old to new')
            length = Choice('length', extra={'select':{'length':'Length(content)'}})
        

"""

class ListSortedMixin(object):
    """
    Mixin for generic class-based views (e.g. django.views.generic.ListView) that can be sorted
    """
    sort_class = Sort
    default_order = None
    
    def __init__(self, order_by=None):
        if order_by:
            self.order_by = order_by
        elif hasattr(self, 'Sort'):
            order_by = dict((k,v) for k, v in self.Sort.__dict__.iteritems() if isinstance(v, Choice))
            self.order_by = order_by
    
    def get_order_by(self, queryset):
        request = self.request
        return self.sort_class(queryset, self.order_by, request=request)
    
    def sort_queryset(self, queryset, sort):
        sortchoice = self.kwargs.get('sort') or self.request.GET.get('sort') or self.default_order or sort.default
        try:
            sort.object_list = queryset
            sort.sort_object_list(sortchoice)
            sortchoice_obj = sort.get_choice(sortchoice)
            return (sort, sortchoice_obj, sort.object_list, bool(self.order_by))
        except InvalidChoice:
            raise Http404(_(u'Invalid ordering choice (%(sortchoice)s)') % {
                                'sortchoice': sortchoice
            })
        
        
    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        context = {}
        queryset = kwargs.pop('object_list')
        
        order_by = self.get_order_by(queryset)
        if order_by:
            sort, sortchoice, queryset, is_sorted = self.sort_queryset(queryset, order_by)
            context.update({
                'sort': sort,
                'sortchoice_obj': sortchoice,
                'is_sorted': is_sorted,
                'object_list': queryset
            })
        else:
            context.update({
                'sort': None,
                'sortchoice_obj': None,
                'is_sorted': False,
                'object_list': queryset
            })
        
        context.update(kwargs)
        context_object_name = self.get_context_object_name(queryset)
        if context_object_name is not None:
            context[context_object_name] = queryset
        return context

    
    
class ListSortedView(ListSortedMixin, ListView):
    """
    A list view that can be sorted
    """
    def get_context_data(self, **context):
        context = ListSortedView.get_context_data(self, **context)
        context = ListView.get_context_data(self, **context)
        return context