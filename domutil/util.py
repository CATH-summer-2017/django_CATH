# from modeller import *
# from modeller.scripts import complete_pdb
# ### Enable this line to reduce verbositys
# # log.none()
import sys,os
import StringIO
import contextlib
import re 
import numpy as np

full = lambda p: os.path.expandvars(p)

p_nb = re.compile("Number of non-bonded pairs \(excluding 1-2,1-3,1-4\): *([0-9]*)")
p_energy=re.compile("Current energy *: *([0-9,\.,-]*)")
p_atomCount = re.compile("Number of all, selected real atoms *: ([0-9, ]{10})")
p_resCount = re.compile("Number of all residues in MODEL *: *([0-9]*)")
p_header = re.compile("NAME.*?\n")
p_hmmlen = re.compile('LENG  (\d+)\n')
p_cathdomain = re.compile("([0-9,a-z,A-Z]{7})")

levels=[ None,
'root',
'Class',
'arch',
'topo',
'homsf',
's35',
's60',
's95',
's100'];

@contextlib.contextmanager
def stdoutIO(stdout=None):
    oldout = sys.stdout
    olderr = sys.stderr
    if stdout is None:
        stdout = StringIO.StringIO()
    sys.stdout = stdout
    sys.stderr = stdout
    yield stdout
    sys.stdout = oldout
    sys.stderr = olderr


import urllib2
def get_gzip(url = 'http://download.cathdb.info/cath/releases/daily-release/newest/cath-b-s35-newest.gz'):

# putative_s35_url = 'http://download.cathdb.info/cath/releases/daily-release/newest/cath-b-s35-newest.gz'
# url = 'http://download.cathdb.info/cath/releases/daily-release/newest/cath-b-s35-newest.gz'
    request = urllib2.Request( url)
    response = urllib2.urlopen(request)
    request.add_header('Accept-encoding', 'gzip')
    request.add_header('Accept-encoding', 'gz')
    response = urllib2.urlopen(request)
    if response.info().get('content-type') == 'application/x-gzip':
#     if 1:
        buf = StringIO.StringIO(response.read())
        f = gzip.GzipFile(fileobj=buf)
        data = f.read()# len(f)
    else:
        data = response.read()
    # type(f)
    # help(f)
    # lines = data.splitlines()
    mapdict = {}
    return data

import sys
class counter():
    def __init__(self, lst, per = 100, fper = 1, INF = False, stdout = sys.stdout,
    	ifprint = 1,
        prefix = '' ):
        # self.lst = list(lst);
        # self.imax= len(lst)
        if INF:
            self.imax = -1
        else:
            self.imax= sum( 1 for _ in lst)
        self.i   = 0
        self.f   = 0
        self.per = per
        self.fper = fper
        self.flst = []
        self.e = None
        self.stdout = stdout
        self.ifprint = ifprint
        self.prefix = prefix 


    def count(self):
        if not self.i % self.per and self.ifprint:
            msg = '%d of %d'%(self.i,self.imax)
            msg = self.prefix + msg
            print >> sys.__stdout__, msg
            print >> self.stdout, msg
        self.i += 1
    def fail(self, msg, ins = None):
     #    if not self.f % self.fper:
        if msg:
            msg = self.prefix + msg
            print >> sys.__stdout__, msg
            print >> self.stdout, msg
        self.f += 1
        self.flst += [ins]
        try:
            self.e = e
        except:
            pass
    def finish(self):
        self.imax = self.i

import csv

def csv_listener( q, fname):
    '''listens for messages on the q, writes to file. '''
    ## Read "fname" from global. "fname" file must exists prior to call.

    f = open(fname, 'a') 
    c = csv.writer(f)
    while 1:
        m = q.get()
        if m == 'kill':
            # f.write('killed \n')
            break
        elif m == 'clear':
            f.truncate();    
        else:## Asumme a csv row
            row = m
            c.writerow( row )
        f.flush()
    f.close()



def worker( i, q, slist):
    # global wait, waitname
    # pdbfile = onlyfiles[i];
    (wait,waitname,reset,fname,env,args) = slist

    pdbfile = i;
    import os 

    pdbname = os.path.basename(pdbfile);
    if pdbname.split(".")[-1] in ["bak","csv"]:
        return 
    if wait:
        nDOPE = 0
        if pdbname == waitname:
            q.put('start');
            nDOPE = get_nDOPE( pdbfile, env = env, auto_complete = args.auto_complete)
        row = [pdbname, nDOPE ];

    else:    
        # print("\n\n//Testing structure from %s" % pdbfile)
        nDOPE = get_nDOPE( pdbfile, env = env, auto_complete = args.auto_complete)                
        row = [pdbname, nDOPE] ;
    q.put( row );
    
    return row



### Statistics helper functions

def MAD_outlier(points, thresh=3.5):
    """
    Returns a boolean array with True if points are outliers and False 
    otherwise.

    Parameters:
    -----------
        points : An numobservations by numdimensions array of observations
        thresh : The modified z-score to use as a threshold. Observations with
            a modified z-score (based on the median absolute deviation) greater
            than this value will be classified as outliers.

    Returns:
    --------
        mask : A numobservations-length boolean array.

    References:
    ----------
        Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
        Handle Outliers", The ASQC Basic References in Quality Control:
        Statistical Techniques, Edward F. Mykytka, Ph.D., Editor. 
    """
    if not isinstance(points,np.ndarray):
        points = np.array(points)
    if len(points.shape) == 1:
        points = points[:,None]
    median = np.median(points, axis=0)
    diff = np.sum((points - median)**2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation

    return modified_z_score > thresh


def cov2corr(c):
    c = np.copy(c)
    try:
        d = np.diag(c)
    except ValueError:
        # scalar covariance
        # nan if incorrect value (nan, inf, 0), 1 otherwise
        return c / c
    stddev = np.sqrt(d.real)
    c /= stddev[:, None]
    c /= stddev[None, :]

    # Clip real and imaginary parts to [-1, 1].  This does not guarantee
    # abs(a[i,j]) <= 1 for complex arrays, but is the best we can do without
    # excessive work.
    np.clip(c.real, -1, 1, out=c.real)
    if np.iscomplexobj(c):
        np.clip(c.imag, -1, 1, out=c.imag)

    return c







" Here starts ISS utils"
from Bio import SearchIO
#### import hmmpf database
# print("finished")
hmmpf_file = full("$SEQlib/cath-S35-hmm3.lib")
# hmmpf_file = full("$SEQlib/tmp.hmmpf")

def search_idx(q_acc, fname, acc_func):
    # fname = f
    with open( full(fname) , 'r') as f:
        line = f.readline()
        idx = 0
        while line:
#             header = line.rstrip("\n")[6:]
#             acc = seqheader_parse_cath(header)["acc"]
            acc = acc_func(line)
            if acc == q_acc:
                break
            
            line = f.readline()
            idx += 1
        if not line:
            return None
        else:
            return idx
        
        

        
import subprocess
def index_hmmlib(hmmlib_file):
    idxfile = hmmlib_file + '.idx'
    if not os.path.isfile(idxfile):
        subprocess.call(['cat',hmmlib_file,'|','grep','NAME','>',idxfile])
    f = open(idxfile,'r')
    lines = f.readlines()
    f.close() 
    return lines


def search_lib( q_acc, hmmlib_file = hmmpf_file, acc_func = None):
    
    ##### check whether an index file exists *.idx
    idxfile = hmmlib_file + '.idx'
    if not os.path.isfile(idxfile):
        subprocess.call(['cat',hmmlib_file,'|','grep','NAME','>',idxfile])
    if not acc_func:
        acc_func = lambda line: seqheader_parse_cath(line.rstrip("\n")[6:])["acc"]
    
    idx = search_idx(q_acc ,idxfile, acc_func)
    print idx

    if not idx:
        return None
    else:
        with open( full(hmmlib_file) ,'r') as f:
            line = 1
            cidx = 0
#             ln = 0
            buf = ""
            while line:
                line = f.readline()                
                if cidx == idx:
                    buf += line
                if line.rstrip('\n')=='//':
                    cidx += 1
                    if buf:
                        return buf 



#### import sequence database
def seqheader_parse_cath(header):
    lst = header.split("|")
#     dbname = lst[0]
    dbname = "CATH"
    version = 'v' + lst[1]
    acc = lst[2].split("/")[0] 
    jdict = {
        "seqDB":{
            "name":   dbname,
            "version":version,        
            },
        "acc": acc,
        }
    return jdict

def parse_hmmlib(fname):
    with open(fname, "r") as f:
        buf = ''
        while 1:
            line = f.readline()
            buf += line
            if line == '//\n':
                yield buf
                buf = ''
            if not line:
                break

# import gc
def hsp2jdict(hsp,query = None, simple = False):
    jdict = hsp.__dict__
    if not simple:
	    jdict["query_id"] = query.id
	#     print hsp.hit_id
	    jdict["target_id"] = hsp.hit_id
    # jdict["target_id"] = sequence.objects.get( acc = hsp.hit_id).id
    it = jdict.pop('_items')
    jdict.pop('domain_index')
    jdict["start"]=jdict.pop("env_start")
    jdict["end"]=jdict.pop("env_end")
    jdict["logCevalue"] = max(-1000,np.log10(jdict.pop("evalue_cond")))
    jdict["logIevalue"] = max(-1000,np.log10(jdict.pop("evalue")))
    
    return jdict



def hmmsearch(hmm,seqDB_curr = None, seqDB_file = None, tmpdir = "/tmp", 
	tbl_format = 'hmmsearch3-domtab'):
#     if ["seqDB_curr"] in locals().keys():
    if not seqDB_curr:
        seqDB_curr = seqDB.objects.get(name = 'CATH')
#         seqDB_file = seqDB_curr.filepath
    if seqDB_file:
        seqDB_file = full(seqDB_file)
    

    tmphmm = "%s/hmm" % tmpdir
    with open(tmphmm,'w') as f:
        f.write(hmm.text)
    cmd = ["hmmsearch","--noali","-o",tmpdir+"/log","--domtblout",tmpdir + "/domtbl", 
                                     tmphmm, seqDB_file,]
    # print ' '.join(cmd)
    try:
        qtext = subprocess.check_output( cmd )
    except Exception as e:
    	print 'CMD is: %s' % (' '.join(cmd))
        raise e 
    # del qtext
    # gc.collect()

    parser = SearchIO.parse( tmpdir + "/domtbl", tbl_format )
    
    q_hits = next(parser,None)
    if q_hits:
	    q_hits.id = seqheader_parse_cath(q_hits.id)["acc"]
	    def acc_mapper(hit):
	#         hit.query
	        hit.id = seqheader_parse_cath(hit.id)["acc"]
	        return hit
	    q_hits = q_hits.hit_map(acc_mapper)
	    return q_hits
    
	# oldhits = hmm.hit4hmm2hsp_set.all()
	# for hit in q_hits:
	#     hsp = hit[0] ### Assume only one dom per hit
	#     jdict = hsp2jdict(hsp, query = hmm )
	#     jdict["target_id"] = sequence.objects.get( acc = jdict["target_id"]).id
	#     if not oldhits.filter(**jdict).exists():
	#         hit_db = hit4hmm2hsp(**jdict)
	#         hit_db.save()

#     dis_q = hmm.hit4hmm2hsp_set.values_list("target",flat = True).distinct()
    
#     q = hmm.hit4hmm2hsp_set.all()

#     if dis_q.count() < q.count():
#         q = q.exclude(id__in=list(dis_q.values_list("id",flat = True)) )
# #         q.delete()
# #         dis_q.update()
        
    # return hmm.hit4hmm2hsp_set

def batch_qs(qs, batch_size=1000):
    """
    Returns a (start, end, total, queryset) tuple for each batch in the given
    queryset.
    
    Usage:
        # Make sure to order your querset
        article_qs = Article.objects.order_by('id')
        for start, end, total, qs in batch_qs(article_qs):
            print "Now processing %s - %s of %s" % (start + 1, end, total)
            for article in qs:
                print article.body
    """
    total = qs.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        # yield (start, end, total, qs[start:end])
        yield qs[start:end]
def acc_mapper_cath(hit):
#         hit.query
    hit.id = seqheader_parse_cath(hit.id)["acc"]
    return hit    






##### iterating over COO sparse matrix (10 times faster than DOK matrix)

import random
import itertools

# def using_nonzero(x):
#     rows,cols = x.nonzero()
#     for row,col in zip(rows,cols):
#         ((row,col), x[row,col])

# def using_coo(x):
#     cx = scipy.sparse.coo_matrix(x)    
#     for i,j,v in zip(cx.row, cx.col, cx.data):
#         (i,j,v)

def using_tocoo(x):
    cx = x.tocoo()    
    it = zip(cx.row, cx.col, cx.data)
    return it
    # for i,j,v in zip(cx.row, cx.col, cx.data):
    #     (i,j,v)

def using_tocoo_izip(x):
    cx = x.tocoo() 
    it = itertools.izip(cx.row, cx.col, cx.data)
    return it   
    # for i,j,v in itertools.izip(cx.row, cx.col, cx.data):
    #     yield (i,j,v)
