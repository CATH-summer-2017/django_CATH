from tst.utils_db import *
from time import time
from tst.domutil.util import *

# v_curr = verify_version('putative')
v_curr = verify_version('test')


#### Calculate superfamily-based statistics

t0 = time()



lst = domain.objects.filter( classification__version = v_curr )
behave = "Calculating structure-based stats"

print("%s for %d from verion: %s" % (behave, len(lst), v_curr.name))


# lst = lst[:50]
c = counter(lst, per = 10)
failcount = 0


debug = 1
import sys
# s0 = stdoutIO()
# stdoutIO()
from Bio.PDB import PDBParser
parser = PDBParser()
with stdoutIO() as s0:
	with transaction.atomic():
		for d in lst:
			c.count()
			try:
				domain_stat_fill(d,s0 = s0, parser = parser)
			except Exception as e:
				if debug: print >>sys.__stdout__,e,d.domain_id
				failcount += 1




print '%d instances of %d failed' % (failcount,c.imax)
print('Ended after %.4f' % (time()-t0))  # len(lst)d

failrate = failcount/float(c.imax) 
assert failrate < 0.1.'fail rate is too high: expected < 10%, actual: %2.2f%%' % failrate

# homsf_stat_fill(lst[0])
# print(str(lst[0]))
## 4p0fA02
## 4au2B02