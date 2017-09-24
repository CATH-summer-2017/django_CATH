import re
from django import template
from django.conf import settings

register = template.Library()

from tst.domutil import util

# numeric_test = re.compile("^\d+$")
# def getattribute_none(value, arg):
#     """Gets an attribute of an object dynamically from a string name"""
#     if hasattr(value, str(arg)):
#         attr = getattr(value, str(arg));
#         if callable(attr):
#             return attr();
#         else:
#             return attr
#     elif hasattr(value, 'has_key') and value.has_key(arg):
#         return value[arg]
#     elif numeric_test.match(str(arg)) and len(value) > int(arg):
#         return value[int(arg)]
#     else:
#         return 'None'

# def getattribute(value, arg):
#     """Gets an attribute of an object dynamically from a string name"""
#     if arg.endswith("?"):
#         arg = arg[:-1]
#         callit = 1
#     else:
#         callit = 0

#     if hasattr(value, str(arg)):
#         attr = getattr(value, str(arg));
#         # tp = type(attr) 
#         # if callable(attr) and tp != "django.db.models.manager.Manager":
#         if callit:
#             return attr();
#         else:
#             return attr
#     elif hasattr(value, 'has_key') and value.has_key(arg):
#         return value[arg]
#     elif numeric_test.match(str(arg)) and len(value) > int(arg):
#         return value[int(arg)]
#     else:
#         return settings.TEMPLATE_STRING_IF_INVALID + ' ' + arg

# def getattribute_iter(value, args):
#     args = args.split('__');
#     # value 
#     for arg in args:
#         if arg:
#             value = getattribute(value,arg);
#         else:
#             pass

#     return value

# @register.filter
def get_type(value):
    return type(value).__name__

@register.filter(name = 'to_class_name')
def to_class_name(value):
    return value.__class__.__name__

register.filter('getattribute', util.getattribute)
register.filter('getattribute_iter', util.getattribute_iter)
register.filter('getattribute_none', util.getattribute_none)
register.filter('get_type', get_type)
register.filter('to_class_name', to_class_name)
