# Resources imports
from django.contrib.admin.sites import site
from django.views.generic import View as BaseView, ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin
from django.conf.urls.defaults import include, url, patterns
from django.core.urlresolvers import reverse_lazy
from tartarus.string import camelcase_split
from tartarus.utils import config, set_attributes_to_inner_classes, get_leaf_subclasses
import inspect
import operator

# Autodiscover imports
import copy
from django.conf import settings
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule


class Resource(object):
    
    default = 'default'
    
    def __init__(self, *args, **kwargs):
        self.set_defaults(**kwargs)
    
    def set_defaults_views(self):
        has_slug = hasattr(self, 'slug_field')
        has_detail = False
        for name, member in inspect.getmembers(self, inspect.isclass):
            if issubclass(member, BaseView):
                if not hasattr(member, 'name'):
                    member.name = self.get_system_name(name)
                if not hasattr(member, 'pattern'):
                    if issubclass(member, SingleObjectMixin) and not issubclass(member, CreateView):
                        if has_slug:
                            pattern = r'(?P<%s>[-\w]+)/' % member.slug_field
                        else:
                            pattern = r'(?P<pk>\d+)/'
                        if not has_detail and issubclass(member, DetailView):
                            pattern += '?'
                            has_detail = True
                        else:
                            pattern += member.name
                    else:
                        pattern = member.name
                    member.pattern = pattern+'$'
                if not hasattr(member, 'url_name'):
                    member.url_name = '%s#%s' % (self.name, member.name)
                if not hasattr(member, 'resource'):
                    member.resource = self
    
    def set_defaults(self, **kwargs):
        config(self, **kwargs)
        if not hasattr(self, 'name'):
            self.name = self.get_system_name(self)
        if not hasattr(self, 'pattern'):
            self.pattern = self.name
        self.set_defaults_views()
    
    @classmethod
    def get_system_name(self, whatever):
        if not isinstance(whatever, str):
            if isinstance(whatever, object):
                whatever = whatever.__class__
            if isinstance(whatever, type):
                whatever = whatever.__name__ 
        return camelcase_split(whatever, '-')
    
    def get_views(self):
        views = {member.name: member for name, member in inspect.getmembers(self, inspect.isclass) if issubclass(member, BaseView)}
        return views
    
    def get_default_view(self):
        views = self.get_views()
        if views.has_key(self.default):
            return views[self.default]
    
    def get_urls(self):
        views = self.get_views().values()
        urls = []
        for view in views:
            if view.name == self.default:
                pattern = '$'
            else:
                pattern = getattr(view, 'pattern', view.name)
            urls.append(
                url(
                    pattern,
                    view.as_view(),
                    name=view.url_name
                )
            )
        
        #Sort it for url matching
        urls_sort_dict = {}
        for i, u in enumerate(urls):
            level = u.regex.pattern.count('/')
            urls_sort_dict[i] = level
        sorted_urls = []
        for k, i in sorted(urls_sort_dict.iteritems(), key=operator.itemgetter(1)):
            sorted_urls.insert(i, urls[k])
        sorted_urls.reverse()
        pattern = getattr(self, 'pattern', self.name).strip()
        if len(pattern) > 0:
            pattern = '^%s/' % pattern
        return url(pattern, include(sorted_urls))


class ModelResource(Resource):
    
    default = 'list'
    
    #'succes_url' is only for edit views like Create, Update and Delete
    single_attributes = ['model', 'queryset', 'slug_field', 'context_object_name', 'success_url']
    multiple_attributes = ['allow_empty', 'model', 'queryset', 'paginate_by', 'context_object_name', 'paginator_class']
    
    def __init__(self, **kwargs):
        super(ModelResource, self).__init__(**kwargs)
        
        if not hasattr(self, 'success_url'):
            self.success_url = reverse_lazy(self.get_default_view().url_name)
        
        set_attributes_to_inner_classes(self, self.single_attributes, SingleObjectMixin)
        set_attributes_to_inner_classes(self, self.multiple_attributes, MultipleObjectMixin)
    
    class List(ListView):
        pass
    
    class Detail(DetailView):
        pass
    
    class Create(CreateView):
        pass
    
    class Update(UpdateView):
        pass
    
    class Delete(DeleteView):
        pass
    

class View(TemplateView):
    pass

class ResourceHelper(object):
    @classmethod
    def update_context_data(self, view, context):
        context.update({'resource':view.resource.name,'view':view.name})

def autodiscover(root=True, filter=None):
    """
    Auto-discover INSTALLED_APPS views.py modules and fail silently when
    not present. This forces an import on them to register any views bits they
    may want.
    """

    # Try to load root views
    if root and settings.PROJECT_NAME not in settings.INSTALLED_APPS:
        load_app_views(settings.PROJECT_NAME)
    # Load apps views
    for app in settings.INSTALLED_APPS:
        load_app_views(app)

    leafs = get_leaf_subclasses(Resource, filter=filter)
    resources = [r() for r in leafs if r is not ModelResource]
    resource_patterns = []
    for r in resources:
        resource_patterns += patterns('', r.get_urls())
    return resource_patterns


def load_app_views(app=None):
    if app:
        mod = import_module(app)
    else:
        mod = False
        app = settings.PROJECT_NAME
    views_module = '%s.views' % app
    
    # Attempt to import the app's admin module.
    try:
        before_import_registry = copy.copy(site._registry)
        import_module(views_module)
    except:
        # Reset the model registry to the state before the last import as
        # this import will have to reoccur on the next request and this
        # could raise NotRegistered and AlreadyRegistered exceptions
        # (see #8245).
        site._registry = before_import_registry

        # Decide whether to bubble up this error. If the app just
        # doesn't have an views module, we can ignore the error
        # attempting to import it, otherwise we want it to bubble up.
        if mod and module_has_submodule(mod, 'views'):
            raise