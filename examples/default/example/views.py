from tartarus.django.resources import Resource, View
from django.conf import settings

class Home(Resource):
    pattern = ''
    class Default(View):
        template_name = 'home.html'
        def get_context_data(self, **kwargs):
            return {
                'project_name': settings.PROJECT_NAME
            }