from django.views.generic import ListView
from tartarus.django.pagination import Paginator

"""
Based on https://github.com/jamespacileo/django-pure-pagination
"""
    
class ListPaginatedMixin(object):
    """
    Mixin for generic class-based views (e.g. django.views.generic.ListView) that can be paginated
    """
    # Replace the default django.core paginator by Paginator
    paginator_class = Paginator

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True):
        # Pass the request object to the paginator to keep the parameters in the url querystring ("?page=2&old_param=...")
        request = self.request
        return self.paginator_class(queryset, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page, request=request)

    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        context = {}
        queryset = kwargs.pop('object_list')

        page_size = self.get_paginate_by(queryset)
        if page_size:
            paginator, page, queryset, is_paginated = self.paginate_queryset(queryset, page_size)
            context.update({
                'paginator': paginator,
                'page_obj': page,
                'is_paginated': is_paginated,
                'object_list': queryset
            })
        else:
            context.update({
                'paginator': None,
                'page_obj': None,
                'is_paginated': False,
                'object_list': queryset
            })
        
        context.update(kwargs)
        context_object_name = self.get_context_object_name(queryset)
        if context_object_name is not None:
            context[context_object_name] = queryset
        return context

class ListPaginatedView(ListPaginatedMixin, ListView):
    """
    A list view that can be paginated
    """
