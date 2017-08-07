from tst.models import *
domain_stat.objects.all().delete()
node_stat.objects.all().delete()
domain.objects.all().delete()
classification.objects.filter(version__id__gt=1).delete()