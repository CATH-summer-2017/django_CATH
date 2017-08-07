# from tst.domutil.utils import *
# from tst.utils import *
from tst.domutil.util import *
from tst.utils_db import *
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

with transaction.atomic():
#     cc=0
    lines = data.splitlines()[:2000]
    c = counter(lines, per = 1000)
    for line in lines:
        n,conf = parse_domain(line, v_curr)
        confcount += conf
        c.count()
    #     pass
    #     print(line)
        pass
print()