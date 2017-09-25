
import sys
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
USE_MODELLER = 0
os.environ['USE_MODELLER']  = '%d'%USE_MODELLER

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
	#'mptt',
)

if os.getenv('TRAVIS', None):
	#################################################################################
	# DO NOT EDIT this. This configuration is only used when submited to travis-CI ##
	#################################################################################
	SECRET_KEY = "SecretKeyForUseOnTravis"
	DEBUG = False
	TEMPLATE_DEBUG = True

	DATABASES['default'] = {
			'ENGINE': 'django.db.backends.mysql',
			'NAME': 'django',
			'TEST':{
				'NAME':'test_django'
				},
			# 'USER': 'root',
			'USER': 'travis',
			'PASSWORD': '',
			'HOST': '127.0.0.1',
			# 'PORT': '3306',
		}
else:
	#Non-travis DB configuration goes here
	#####################################################################################
	### !!!   Please edit here to configure database backend your database config !!!####
	#####################################################################################
	DATABASES['default'] = {
	    'ENGINE': 'django.db.backends.mysql', #### Use of a MySQL as backend is assumed here.
	    'NAME': 'django',   		  #### Name of the MySQL database goes in here.
		'TEST': {
		    'NAME': 'test_django',        #### Name of the MySQL database for testing goes in here.
		    },            
	    'USER': 'django',   		  #### Username that Django should be using to connect to your MySQL
	    'PASSWORD': 'Django_passw0rd',  	  #### Password that Django should be using to connect to your MySQL
	    'HOST': '127.0.0.1',   		  #### We are assuming a local MySQL (localhost) is being used
	    'PORT': '3306',	   	     	  #### MySQL is default to run on 3306
	}        


ALLOWED_HOSTS += [
'testserver',
'localhost',
'127.0.0.1',
]
