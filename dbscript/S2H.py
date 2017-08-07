from tst.utils_db import *
from time import time

# v_curr = verify_version('putative')
v_curr = verify_version('test')


#### Calculate superfamily-based statistics

t0 = time()


level_curr = level.objects.get(letter = 'H')
# node_set =  classification.objects.filter(version = v_curr)
node_set =  classification.objects.filter(version__id__lte = v_curr.id)
lst = node_set.filter(level = level_curr)

print("calculating superfamily stats for %d from verion: %s" % (len(lst), v_curr.name))
c = counter(lst, per = 100)
failcount = 0
for d in lst:
    c.count()
    with transaction.atomic():
#     if 1:
        failcount += homsf_stat_fill(d) == 0

print '%d instances failed' % failcount
print('Ended after %.4f' % (time()-t0))  # len(lst)
# homsf_stat_fill(lst[0])
# print(str(lst[0]))