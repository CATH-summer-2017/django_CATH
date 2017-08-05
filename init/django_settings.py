
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'GB'
USE_I18N = True
USE_L10N = True
USE_TZ = True


STATIC_URL = '/static/'
TEMPLATE_STRING_IF_INVALID = 'No attr:'

INSTALLED_APPS += (
    'tst.apps.Config',
    'django_extensions',
)

DATABASES['default'] = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django',
        'USER': 'django',
        'PASSWORD': 'Django_passw0rd',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
