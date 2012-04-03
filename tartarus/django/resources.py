# Resources imports
from django.contrib.admin.sites import site
from django.views.generic import View as BaseView
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views.generic.list import MultipleObjectMixin, MultipleObjectTemplateResponseMixin
from django.conf import settings
from django.conf.urls.defaults import include, url, patterns
from django.core.urlresolvers import reverse_lazy
from tartarus.django.views import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from tartarus.string import camelcase_split
from tartarus.utils import config, set_attributes_to_inner_classes, get_leaf_subclasses, underscore_to_label
from django.utils.encoding import StrAndUnicode
import operator
import os

# Autodiscover imports
import copy
from django.conf import settings
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule
import inspect

class ResourceContext(str, StrAndUnicode):
    def __unicode__(self):
        return self.name

class ResourceViewMixin(object):
    def get_context_data(self, **kwargs):
        context = {'resource':self.resource.get_context_representation(),'view':self.get_context_representation()}
        context.update(kwargs)
        return context
    def get_template_names(self):
        templates = [ '%s/%s.html' % (self.resource.name, self.name) ]
        return templates
    def get_context_representation(self):
        rc = ResourceContext(self.name)
        content = { 'name': self.name, 'label': self.label}
        config(rc, **content)
        return rc

class Resource(object):
    
    default = 'default'
    
    def __init__(self, *args, **kwargs):
        self.set_defaults(**kwargs)
        
    def get_context_representation(self):
        rc = ResourceContext(self.name)
        content = { 'name': self.name, 'label': self.label, 'default': self.default }
        config(rc, **content)
        return rc
        
    def set_defaults_views(self):
        has_slug = hasattr(self, 'slug_field')
        has_detail = False
        for name, member in inspect.getmembers(self, inspect.isclass):
            if issubclass(member, BaseView):
                if not hasattr(member, 'name'):
                    member.name = self.get_system_name(name)
                if not hasattr(member, 'label'):
                    member.label = underscore_to_label(member.name)
                if not hasattr(member, 'pattern'):
                    if issubclass(member, SingleObjectMixin) and not issubclass(member, CreateView):
                        if has_slug:
                            pattern = r'(?P<%s>[-\w]+)/' % member.slug_field
                        else:
                            pattern = r'(?P<pk>\d+)/'
                        if not has_detail and issubclass(member, DetailView):
                            has_detail = True
                        else:
                            pattern += member.name
                    else:
                        pattern = member.name
                    member.pattern = r'^%s$' % pattern 
                if not hasattr(member, 'url_name'):
                    member.url_name = '%s#%s' % (self.name, member.name)
                if not hasattr(member, 'url_names'):
                    if member.name == self.default:
                        member.alternative_url_names = [ '%s' % self.name ]
                    else:
                        member.alternative_url_names = []
                if not hasattr(member, 'resource'):
                    member.resource = self
    
    def set_defaults(self, **kwargs):
        config(self, **kwargs)
        if not hasattr(self, 'name'):
            self.name = self.get_system_name(self)
        if not hasattr(self, 'label'):
            self.label = underscore_to_label(self.name)
        if not hasattr(self, 'pattern'):
            self.pattern = '^%s/'%self.name
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
                pattern = '^$'
            else:
                pattern = getattr(view, 'pattern', view.name)
                
            view_instance = view.as_view()
            url_names = [ view.url_name ]
            url_names += view.alternative_url_names
            for url_name in url_names:
                urls.append(
                    url(
                        pattern,
                        view_instance,
                        name=url_name
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
        return url(pattern, include(sorted_urls))

class BaseModelResource(Resource):
    #'succes_url' is only for edit views like Create, Update and Delete
    single_attributes = ['model', 'queryset', 'slug_field', 'context_object_name', 'success_url']
    multiple_attributes = ['allow_empty', 'model', 'queryset', 'paginate_by', 'context_object_name', 'paginator_class']
    
    def __init__(self, **kwargs):
        super(BaseModelResource, self).__init__(**kwargs)
        
        if not hasattr(self, 'success_url'):
            self.success_url = reverse_lazy(self.get_default_view().url_name)
        
        set_attributes_to_inner_classes(self, self.single_attributes, SingleObjectMixin)
        set_attributes_to_inner_classes(self, self.multiple_attributes, MultipleObjectMixin)


class ModelResourceViewMixin(ResourceViewMixin):
    def get_template_names(self):
        template_names = []
        if isinstance(self, SingleObjectTemplateResponseMixin):
            template_names += SingleObjectTemplateResponseMixin.get_template_names(self)
        elif isinstance(self, MultipleObjectTemplateResponseMixin):
            template_names += MultipleObjectTemplateResponseMixin.get_template_names(self)
        model_template_name = 'model%s.html' % self.template_name_suffix
        template_names += [ os.path.join(self.resource.name, model_template_name), model_template_name ]
        return template_names


class ModelResource(BaseModelResource):
    
    default = 'list'
    
    class List(ModelResourceViewMixin, ListView):
        paginate_by = 10
        def get_context_data(self, **kwargs):
            context = ListView.get_context_data(self, **kwargs)
            context = ModelResourceViewMixin.get_context_data(self, **context)
            return context
    
    class Detail(ModelResourceViewMixin, DetailView):
        def get_context_data(self, **kwargs):
            context = DetailView.get_context_data(self, **kwargs)
            context = ModelResourceViewMixin.get_context_data(self, **context)
            return context
    
    class Create(ModelResourceViewMixin, CreateView):
        def get_context_data(self, **kwargs):
            context = CreateView.get_context_data(self, **kwargs)
            context = ModelResourceViewMixin.get_context_data(self, **context)
            return context
    
    class Update(ModelResourceViewMixin, UpdateView):
        def get_context_data(self, **kwargs):
            context = UpdateView.get_context_data(self, **kwargs)
            context = ModelResourceViewMixin.get_context_data(self, **context)
            return context
    
    class Delete(ModelResourceViewMixin, DeleteView):
        def get_context_data(self, **kwargs):
            context = DeleteView.get_context_data(self, **kwargs)
            context = ModelResourceViewMixin.get_context_data(self, **context)
            return context
    


class ResourceView(ResourceViewMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        context.update(ResourceViewMixin.get_context_data(self, **context))
        return context
    
    def get_template_names(self):
        template_names = ResourceViewMixin.get_template_names(self)
        template_names +=  TemplateView.get_template_names(self)
        return template_names

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