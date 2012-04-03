from tartarus.django.views.pagination import ListPaginatedMixin
from tartarus.django.views.sort import ListSortedMixin
from tartarus.django.views.filter import ListFilteredMixin
from django.views.generic import ListView

class ListView(ListSortedMixin, ListFilteredMixin, ListPaginatedMixin, ListView):
    def get_context_data(self, **context):
        context = ListSortedMixin.get_context_data(self, **context)
        context = ListFilteredMixin.get_context_data(self, **context)
        context = ListPaginatedMixin.get_context_data(self, **context)
        return context