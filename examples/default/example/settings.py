from tartarus.django.conf.settings.default import *

INSTALLED_APPS += (
    PROJECT_NAME,
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

TEMPLATE_DIRS += (
    PROJECT_ROOT + '/' + 'templates',
)