from tst.domutil.util import *
def make_testfile(data, sfnode):
    lines = data.splitlines()
    newlines = []
    for l in lines:
        lst = l.split()
        domain_id = lst[0]
        node_str = lst[1] 
        if node_str.split('.')[:4] in sfnode:
#         nodelst = node_str.split('.') 
#         nodelst += ( 9 - len(nodelst)) * ['1']
#         l = [lst[0]] + nodelst + ['0','0'] 
#         newlines += ['     '.join(l)]
            newlines += [l]
    return('\n'.join(newlines))

sflist = [
"1.10.30.10",
"1.10.60.10",
"2.30.39.10",
"3.30.497.10",]

sfnodes = [x.split('.') for x in sflist]


data = get_gzip('http://download.cathdb.info/cath/releases/daily-release/newest/cath-b-s35-newest.gz')

d = make_testfile(data, sfnodes)
with open('tst/static/test_s35list.txt','w') as f:
    f.write(d)
