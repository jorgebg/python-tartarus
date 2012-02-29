from tartarus.django.conf.settings.pico import *
from tartarus.django.resources import Resource, View, autodiscover

class Home(Resource):
    pattern = ''
    class Default(View):
        template_name = 'home.html'
        def get_context_data(self, **kwargs):
            return {
                'project_name': PROJECT_NAME
            }


urlpatterns += autodiscover()