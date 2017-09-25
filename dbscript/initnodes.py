# from tst.domutil.utils import *
# from tst.utils import *
from tst.domutil.util import *
from tst.utils_db import *
from time import time
t0 = time()

v_curr = verify_version('test')
# data = get_gzip()
# url
import os
url = 'file://' + os.path.abspath('./tst/static/test_s35list.txt')

behave = "initiating hierarchial data"
print("%s for %s from verion: %s" % (behave, url, v_curr.name))
confcount = 0


		

data = get_gzip(url)
mapdict = {}

failcount = 0
with transaction.atomic():
#	 cc=0
	# lines = data.splitlines()[:2000]
	lines = data.splitlines()
	c = counter(lines, per = 1000)
	for line in lines:
		try:
		    lst = line.split()
		    jdict = {
		     domain_id : lst[0] ,
		     homsf_str : lst[1] ,   
		     chopping  : lst[2] ,
		    }
			n,conf = parse_domain( jdict, v_curr)
			confcount += conf
		except:
			failcount += 1
		c.count()
	#	 pass
	#	 print(line)
		pass

failrate = failcount/float(c.imax) 

print "%d nodes in conflict" % confcount
assert failrate < 0.1, 'fail rate is too high: expected < 10%%, actual: %2.2f%%' % failrate
print('Ended after %.4f sec' % (time()-t0))  # len(lst)d
