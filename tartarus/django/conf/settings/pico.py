from tartarus.django.conf.settings.default import PROJECT_NAME, PROJECT_ROOT, TEMPLATE_DIRS, STATIC_URL

DEBUG=True
ROOT_URLCONF = __name__
DATABASES = { 'default': {} }

INSTALLED_APPS = (
    PROJECT_NAME,
    'django.contrib.staticfiles',
)


TEMPLATE_DIRS += (
    PROJECT_ROOT,
)

urlpatterns = []