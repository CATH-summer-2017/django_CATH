from .models import *
from domutil.util import *
from domutil.test import *
# from utils import *
import numpy as np 
from django.db import transaction
import os ,sys


from django.conf import settings
def iter_filter(qset, **filters):
    for k,v in filters.iteritems():
        qset = qset.filter(**{k:v})
    return qset
    # hit4cath2cath.objects.values_list('node1__id'.'node2__id')
    # qset = hit4cath2cath.objects.exclude(node1__parent=F("node2__parent") ) 
    # qset = CCXhit.exclude(ISS_norm__gte=0.9) 

    # qset = CCXhit.filter(ISS_norm__lte=0.9) 

    qset = qset.order_by('-ISS_norm')
    qset = qset[:500]
    return qset


def verify_version(ver):
    #### Check whether this version is recorded in 'version' table
#     try:
    vset = version.objects.filter(name=ver)
    if vset.count() > 1:
        raise Exception,'multiple version with name %s'%(ver)
    elif not vset.exists():
        v = version(name=ver)
        v.save()
    else:
        v = vset[0]
    return v



def hit_summary_fill(d):

    dstat = domai(domain = d);
    dstat.save()
    return dstat

### Fill structure-based stats
def domain_stat_null(d):
    dstat = domain_stat(domain = d);
    dstat.save()
    return dstat
    # if d.domain_stat == None:

### Do not import during test
# if int(settings.TESTING):
#     pass
# else:

# if 1:
from domutil.pdbutil import *

if not settings.USE_MODELLER:

    def domain_stat_fill( d, **kwargs):
        
        ### Using biopython to parse
        struct = parse_PDB(str(d.domain_id),**kwargs)
        outdict = get_something( struct , **kwargs)

        try:
            dstat = d.domain_stat
        except:
            dstat = domain_stat_null(d);


        for k,v in outdict.iteritems():
            if hasattr(dstat,k):
                setattr(dstat, k, v)
        dstat.save()
        return d
else:
    print("settings.USE_MODELLER")

    def domain_stat_fill( d, **kwargs):
        
        ### Using modeller
        outdict = get_something_modeller( str(d.domain_id) , **kwargs)
        
        try:
            dstat = d.domain_stat
        except:
            dstat = domain_stat_null(d);


        for k,v in outdict.iteritems():
            if hasattr(dstat,k):
                setattr(dstat, k, v)
        dstat.save()
        return d

    # from modeller import *
    ### Modeller initialisation

    	



##### !!!!! DEPRECATED !!!!!! 
def homsf_stat_fill(h):
# if 1:
    if h.level.letter == 'H':
        pass
    else:
        print "Node %s is not filled because it is not a homsf, but a '%s'" % (str(h),h.level.letter)
    
    
    try:
        nstat = h.node_stat
    except:
        nstat = node_stat(node = h)
        nstat.save()
        

    hset  = h.classification_set;
    ### Compute statistics only if the set is larger than 10
    if hset.count() > 10:
        hset = hset.annotate(Acount=Avg("domain__domain_stat__atom_count"))
        hset = hset.annotate(Rcount=Avg("domain__domain_stat__res_count"))
        hset = hset.annotate(NBcount=Avg("domain__domain_stat__nbpair_count"))

    #     hset.domain
        l = hset.values_list('Acount','Rcount','NBcount')
        a = np.array(l)
        print >>sys.__stdout__,sum(np.isnan(a).flat)
    #     C = np.cov(a[:,0],a[:,1],a[:,2])
        c = np.cov(a.T)
        C = cov2corr(c); ## utils.cov2corr
#         print(C.shape)
        nstat.Rsq_NBcount_Acount = C[0,2] ** 2
        nstat.Rsq_NBcount_Rcount = C[1,2] ** 2
    else:
        nstat.Rsq_NBcount_Acount = None
        nstat.Rsq_NBcount_Rcount = None
    try:
        nstat.save()
    except:
        print nstat.__dict__
    return h


#### Calculate Mahalanobis distance between the point(pt) and the distribution (mu, cinv), with "mu"=Euclidean_centre AND "cinv"=inversed_covariance_matrix
def maha_dist(pt, mu, cinv):
    dd = pt - mu
    md = dd.T.dot( cinv.dot( dd))
    return md


from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
pip_pc_std = Pipeline([
    ('pca', PCA(n_components=2)),
    ('scaling', StandardScaler()),
                    ])
        
def homsf_stat_fill(h):
#     if 1:
    if h.level.letter == 'H':
        pass
    else:
        print "Node %s is not filled because it is not a homsf, but a '%s'" % (str(h),h.level.letter)


    try:
        nstat = h.node_stat
    except:
        nstat = node_stat(node = h)
        nstat.save()

    hset  = h.classification_set;


    ### Compute statistics only if the set is larger than 10
    hset = hset.exclude(domain__domain_stat__isnull=True)
    if hset.count() > 10:
        hset = hset.annotate(Acount=Avg("domain__domain_stat__atom_count"))
        hset = hset.annotate(Rcount=Avg("domain__domain_stat__res_count"))
        hset = hset.annotate(NBcount=Avg("domain__domain_stat__nbpair_count"))

    #     hset.domain
        l = hset.values_list('Acount','NBcount','Rcount')
        a = np.array(l)
        # sa = a
        c = np.cov(a.T)
        C = cov2corr(c); ## utils.cov2corr
        nstat.Rsq_NBcount_Acount = C[0,1] ** 2
        nstat.Rsq_NBcount_Rcount = C[2,1] ** 2

        sa = a[:,0:2]
        # sa = np.vstack([a[:,0],a[:,1]]).T ### Using only 'Acount' and 'NBcount', discard 'Rcount'
        c = c[:2,:2]

        cinv = np.linalg.inv(c)
        mu = np.mean(sa, axis = 0)

        dstat_set = hset.values_list('domain',flat = True)

        sset = hset ### rename to sset ,aka "s35_set"
    #     qset = domain_stat.objects.none()
        qlst = []
        # print sa.shape
        pcxs,pcys = pip_pc_std.fit_transform(sa).T 

        #### Inverted pc axis if opposing originial x/y axis
        if np.dot(pcys, sa[:,1]) < 0:
            pcys *= -1
        if np.dot(pcxs, sa[:,0]) < 0:
            pcxs *= -1

        for s,pt,pcx,pcy in zip( sset , sa, pcxs, pcys):
            dstat = s.domain.domain_stat
            md = maha_dist( pt, mu, cinv)
            dstat.maha_dist = md
            dstat.pcx = pcx
            dstat.pcy = pcy

    #         print(s.domain)
    #         print(dstat)
    #         print(md)
            qlst.append(dstat)
    #         dstat.save()
    #     qset = list(chain(qset , [dstat]))

    #         print type(qset)

    else:
        nstat.Rsq_NBcount_Acount = None
        nstat.Rsq_NBcount_Rcount = None
        qlst = []

    # help(qset.save)

    # qset.save()
    try:
        nstat.save()
        for q in qlst:
            q.save()
#         print 'success'
        return 1
    except Exception as e:
#         print nstat.__dict__
        print 'failed for ', str(e)
        return 0


import copy
def route_to_node(node_start, node_end, v):
    node = node_start
    lv = node.level.id
    lst = [int(x) for x in node_end.split('.')]
    lst = [0,1,] + lst
    while lv != len(lst)-1:           
        lv += 1           
        ndict = node.node_dict()
        ndict[levels[lv]] = lst[lv]
        node = classification.objects.create(level_id = lv,
                                             version = v,
                                             parent = node,
                                             **ndict)
        node.save()
    # print levels
    return node
       
##### Custom function !!!
def parse_domain(jdict, v = verify_version('test'), rootnode = None):
#     global cc
#     ### verify version
#     ver = 'putative'
#     v = verify_version(ver)
    
    # lst = line.split()
    # domain_id = lst[0]
    # homsf_str = lst[1]    
    # chopping = lst[2]
    
    domain_id = jdict['domain_id']
    homsf_str = jdict['homsf_str']    
    chopping =  jdict.get('chopping',None)

    #### Check whether this node exists in 'classification' table
#     (node,success) = classification.objects.get_bytree(node_str)
    (node,success) = classification.objects.get_bytree(homsf_str, qnode = rootnode)
    
    ### recursively  create new superfamily if not existing
#     print(levels)
    if not success: 
        node = route_to_node( node, homsf_str, v)
#         lv = node.level.id
#         lst = [int(x) for x in homsf_str.split('.')]
#         lst = [0,0] + lst
#         while lv != len(lst)-1:           
#             lv += 1           
#             ndict = node.node_dict()
#             ndict[levels[lv]] = lst[lv]
#             node = classification.objects.create(level_id = lv,
#                                                  version = v,
#                                                  parent = node,
#                                                  **ndict)
#             node.save()
            
#             print('created %s for %s'%(str(node),homsf_str))
#         cc+=1
            
    ####
    conflict = 0
    
    try:
        d = node.domain
        check = 1
    except:
        d = domain.objects.create(classification = node,
                                 domain_id = domain_id,)
        d.save()
        check = 0

    if check:
        # if str(node) in mapdict.keys():
            # pass
        if d.domain_id != domain_id:
            conflict = 1
            
            
            node = copy.copy(node);
            node.pk = None

            lv = node.level.id
            setattr(node, levels[lv],
                    max( node.parent.classification_set.values_list( levels[lv],flat = True ) )+1
                   )
            node.version = v
            node.save()

            d = domain.objects.create(classification = node,
                                 domain_id = domain_id)
            d.save()

        else:
            pass

    return([node,conflict])
    
        
        
    #### if superfamily exists, check whether domain_id agreed
    conflict = 0;
#     print(homsf,homsf_str,success)#     print(line)

    if success:
        pass

    #### Otherwise, write conflict to file










######################################################################
######################################################################
###             ISS               ####################################
######################################################################
######################################################################
######################################################################

def seqheader_guess_parser(header):
    if header.startswith('cath') or header.startswith('CATH') :
        header_parser = seqheader_parse_cath
    
    jdict = header_parser(header)
    seqDB_curr = verify_exist_entry( jdict["seqDB"], seqDB)
    
    return( [header_parser, seqDB_curr])


def verify_exist_entry(dbmodel, **kwargs):
    jdict = kwargs
    #### Check whether this version is recorded in 'version' table
    qset = dbmodel.objects.filter(**jdict)
    if qset.count() > 1:
        raise Exception,'multiple %s with values %s'%( dbmodel, jdict)
    elif not qset.exists():
        v = dbmodel.objects.create(**jdict)
        v.save()
    else:
        v = qset[0]
    return v






##############################################################
## Counting HMM-HMM intermediate sequence ####################
## In other words, counting D_raw     ########################
##############################################################
##############################################################

#### Defining Parallel Wrappers ####

import itertools as itools
from collections import Counter


def batch_worker(seqset,field="cath_node", q = None, c0 = None, c1 = None ):
    count = Counter()
    for seq in seqset:
        c0.count()
        ids = set( seq.hmmprofile_set.values_list( field,flat = True) )
    #             pairs = it.combinations(sorted(hmmids),2)
        pairs = itools.combinations( sorted(ids) ,2)
        count.update(pairs)
    q.put(count)
#     c1.count()
    return 

def seq_counter(seq):
    c0.count()
    hmmids = seq.hmmprofile_set.values_list("id",flat = True)
#             pairs = it.combinations(sorted(hmmids),2)
    pairs = itools.combinations( hmmids ,2)
    count = Counter(pairs)
    q.put(count)
    
    
def listener( OUTPUT, q = None, c0 = None, c1 = None, fdict = None  ):

    counts = Counter([])    
    i = 0

    while 1:
        print i
        i += 1
        obj = q.get()
        if obj:
            c1.count()
            counts.update(obj)            
        else:
            ################################################################
            ###### Put counts into a sparse matrix #########################
            ################################################################     
#             OUTPUT = OUTPUT.todok()]
#             counts
#             d = dict()
            for (x,y),v in counts.iteritems():
                OUTPUT.update({
                    (fdict[x] , fdict[y]) :v
                })
#             OUTPUT.update(counts)
#             q.put( OUTPUT.todok() ) ####### DOK matrix breaks if put on a Queue() for unknown reason
            q.put( OUTPUT.tocoo() )
#             q.put(counts)
            break
    return



from scipy.sparse import dok_matrix
import multiprocessing as mp
from multiprocessing.managers import BaseManager, SyncManager
def draft_hsummary(node, sDB, hcount, node_id = None):
    if node_id:
        node = classifictaion.objects.get(pk = node_id)
    qset = node.hit_summary_set.filter(seqDB=sDB)
    if qset.exists():
        q = qset[0]
        q.hcount = hcount
        q.save()
        return []
    else:
        jdict = {"node": node,
                "seqDB":sDB,
                "hcount":hcount,
                }
        return hit_summary(**jdict)
        # q = hit_summary()
        
class ctmat(object):
    def __init__(self, hmms = None, Cver = None, sDB = None, seqs = None, letter = None, 
        alias = None,
        force = 0,):
        self.force = force 
        if sDB:
            seqs = sDB.sequence_set.all().defer('hmmprofile__text')
            self.sDB = sDB
        else:
            self.sDB = seqs[0].seqDB
        self.sDB_id = self.sDB.id
        self.seqs = seqs
        if Cver:
            hmms = HMMprofile.objects.filter(id__in=Cver.classification_set.values_list('hmmprofile'))
        self.hmms = hmms
        self.D_raw = None
        self.D_norm = None
        self.D_both = None
        self.D_geoavg = None
        self.hits = None
        self.nodes = None
        self.hmmnodes = classification.objects.filter(
            id__in=self.hmms.values_list('cath_node')
            )


        self.cache_hitids = None
        self.cache_hitlist = None
        self.cache_hitdict = None

        self.dump_attrs = [
            "D_raw","D_norm","D_both","D_geoavg","hcounts",
            'cache_hitids','cache_hitlist','cache_hitdict'
        ]
        self.shared_attrs = ['cache_hitids','cache_hitdict']
        
        if letter:
            self.set_letter(letter)
        self.alias = alias or 'test'
        self.name = '%s_%s' % (self.alias, self.letter)
        pass
    
    def dump(self, name = None, attr = None, **kwargs):
        name = name or self.name
        attr = attr or self.dump_attrs

        if not isinstance(attr,list):
            attr = [attr]
        for a in attr:
            if attr in self.shared_attrs:
                fname = '%s/%s' (a, name.rstrip('_'+self.letter))
            else:
                fname = '%s/%s' % (a, name, )
            try:
                var = getattr(self, a)
                if isinstance(var,type(None)):
                    raise Exception("Do not dump a NoneType object ")
                pk_dump( var , fname )
                print "[Msg] managed to dump ""%s"" to %s." % (a, fname)
            except Exception as e:
                print "[Msg] failed  to dump ""%s"" to %s  Exception: '%s' " % (a, fname, e)
    
    def load(self, name =None, attr = None, **kwargs):
        name = name or self.name
        attr = attr or self.dump_attrs

        if not isinstance(attr,list):
            attr = [attr]
        for a in attr:
        #  for f in fields:
            if attr in self.shared_attrs:
                fname = '%s/%s' (a, name.rstrip('_'+self.letter))
            else:
                fname = '%s/%s' % (a, name, )

            try:
                setattr(self, a, 
                pk_load( fname, **kwargs),
                )
                print "[Msg] managed to load ""%s"" from %s" % (a, fname)
            except Exception as e:
                print "[Msg] failed  to load ""%s"" from %s  Exception: '%s' " % (a, fname, e)
    
    def set_letter(self, letter = 'H'):
        self.letter = letter
        self.field = forward_field[letter]
        self.rfield = reverse_field[letter]
        self.reverse_dict = sorted(set( self.hmms.values_list( self.field, flat = True).distinct()))
        self.forward_dict = list2dict( self.reverse_dict )
        self.l = len(self.reverse_dict)
        self.hits = self.seqs.filter(**{"hit4hmm2hsp__query__%s__in" % self.field : self.reverse_dict })
        self.nodes = classification.objects.filter(id__in=self.reverse_dict)
        self.mapper = {}
        self.mapper['node2hitseq'] = self.rfield
        self.mapper['node2hit'] = self.rfield.replace('__hits','__hit4hmm2hsp')
        self.mapper['node2sDB'] = self.rfield + '__seqDB'
        self.mapper['node2hmmnode'] = self.rfield.rstrip('__hmmprofile__hits')
        self.mapper['hmmnode2node'] = self.field.replace('cath_node__','')

        
    def hit_sum(self, dump = 0):
        if isinstance(self.hits, type(None)):
            self.hits = self.seqs.filter(**{"hit4hmm2hsp__query__%s__in" % self.field : self.reverse_dict })
        qset = self.hits.values_list("hit4hmm2hsp__query__%s" % self.field, ).annotate(hcount = Count("id",distinct = True))
        hcounts0 = dict( qset.values_list("hit4hmm2hsp__query__%s" % self.field,"hcount"))
        ex = set(self.reverse_dict) and set(hcounts0.keys())
        self.hcounts = [ hcounts0[i] if i in ex else 0 for i in self.reverse_dict ]
        if dump:
            self.dump( name = self.name, attr = 'hcounts')
        return (hcounts0)
    
    # def hit_sum()
    def OLD_hit_sum(self,):        
        reset_database_connection()
        hcounts = []
        all_nodes = classification.objects.filter(version__name='v4_1_0')
        curr_nodes = all_nodes.filter(level__letter = self.letter).defer(self.rfield.replace("__hits","__text"))
        sids = set(self.sDB.sequence_set.values_list('id',flat = True))

        for node_id in self.reverse_dict:
            qset = curr_nodes.filter(id = node_id)
            hlist = set( qset.values_list(self.rfield, flat =  True) )
            hcount = len( hlist & sids)
            hcounts.append(hcount)
        self.hcounts = hcounts
    
    def Draw_para(self,  bsize = 600, pcount = 5, dump = 0 ):
        class MyManager(SyncManager): pass
        MyManager.register('counter',counter)
        
        field = self.field
        self.seqs = self.seqs.prefetch_related('hmmprofile_set__' + self.field.rstrip('__id') ) 
        
        ##### Actually firing subprocesses #####

        reset_database_connection()
        INPUT = self.seqs
        INPUTs = batch_qs( INPUT, bsize )
        l = self.l
        OUTPUT = dok_matrix( (l + 1, l + 1), dtype = 'int')

        local_listener = listener      
        local_worker = batch_worker
        # print __name__
        # if __name__=='__main__':
        if 1:
                global m
                m = MyManager()
                m.start()
          
                c0 = m.counter( range(INPUT.count()),INF=0, ifprint = 1,  prefix = '[Worker]',
                              per = bsize,)
                c1 = m.counter( [],INF=1, ifprint = 1, prefix = '[Listener]',
                              step = bsize, per = bsize, )
                fdict = m.dict(self.forward_dict)
                q = m.Queue();          

                if 1:
                    pool = mp.Pool( pcount )
                    watcher  = mp.Process( target = local_listener, args = [OUTPUT], kwargs = {'q':q,'c0':c0,'c1':c1,
                                                                              'fdict':fdict
                                                                                              },)
                    watcher.start()
                    jobs = []

                    for INPUT_curr in INPUTs:
                #         job = pool.Process
                        job  = pool.apply_async(local_worker, (INPUT_curr,), {'q':q, 'field': self.field,'c0':c0,'c1':c1,
                                                                             })
                        jobs.append(job)
                    for job in jobs:
                        job.get()

                    q.put(None)
                    watcher.join()
                    OUTPUT = q.get() 
                pool.close()
                pool.join()
                if not self.force:
                    test__raw( OUTPUT, reverse_dict = self.reverse_dict, letter = self.letter, seqDB_curr = self.sDB)
        # D_raw = OUTPUT
        self.D_raw = OUTPUT        
        if dump:
            self.dump( name = self.name, attr = 'D_raw')


        return OUTPUT
    def Dnorm(self, D_raw = None, dump = 0):
        ##### Calculate D_norm from D_raw

        l = self.l
        OUTPUT = dok_matrix( (l+1,l+1), dtype =  np.float)
        ########### it's tricky to check whether "None" has been changed to a numpy array.
        # else:
        #     raise Exception(' A D_raw must be input! ')
        if isinstance(D_raw,type(None)):
            INPUT = self.D_raw
        else:
            INPUT = D_raw

        it  = using_tocoo_izip( INPUT )
        c=counter(it,per=1000)
        it  = using_tocoo_izip( INPUT )
        
        h1s = []
        h2s = []
        h3s = []
        for x,y,v in it:
            c.count()    
            h1s += [self.hcounts[x]]
            h2s += [self.hcounts[y]]
            h3s += [v]

        BUFlst = ISS_normalise_new(
            np.array(h1s),
            np.array(h2s),
            np.array(h3s),
        )


        it  = using_tocoo_izip( INPUT )
        d = dict()
        for (x,y,_),v in izip( it, BUFlst):
            k = (x,y)
            d[k] = v

        OUTPUT.update(d)

        if not self.force:
            test__norm( OUTPUT, self.reverse_dict, self.letter, seqDB_curr = self.sDB,
          norm_func = ISS_normalise_new)
            test__key( OUTPUT )
        self.D_norm = OUTPUT

        if dump:
            self.dump( name = self.name, attr = 'D_norm')       
        return OUTPUT
    
    def Dgeoavg(self, D_raw = None, dump = 0):
        ##### Calculate D_norm from D_raw

        l = self.l
        OUTPUT = dok_matrix( (l+1,l+1), dtype =  np.float)
        
        INPUT = self.D_raw if isinstance(D_raw,type(None)) else D_raw
        # else:
        #     INPUT = D_raw

        it  = using_tocoo_izip( INPUT )
        c=counter(it,per=1000)
        it  = using_tocoo_izip( INPUT )
        
        h1s = []
        h2s = []
        h3s = []
        for x,y,v in it:
            c.count()
            h1s += [self.hcounts[x]]
            h2s += [self.hcounts[y]]

        BUFlst = np.sqrt(
            np.multiply( np.array(h1s) , np.array(h2s))
        )


        it  = using_tocoo_izip( INPUT )
        d = dict()
        
        for (x,y,_),v in izip( it, BUFlst):
            k = (x,y)
            d[k] = v

        OUTPUT.update(d)
        # if not self.force:
        #     test__norm( OUTPUT, self.reverse_dict, self.letter, seqDB_curr = self.sDB,
        #   norm_func = ISS_Dnorm_new)
        #     test__key( OUTPUT )
        self.D_geoavg = OUTPUT
        if dump:
            self.dump( name = self.name, attr = 'D_geoavg')
        return OUTPUT
    def MySQL_hcount(self):
        def callback(buf):
            hit_summary.objects.bulk_create(buf)
            
        reset_database_connection()
        behave = "inserting hit_summary for CATH nodes "
        if isinstance(self.hcounts, type(None)):
            self.hit_sum()
        node_dict = classification.objects.in_bulk(self.reverse_dict)
        
        with transaction.atomic():
            buf = []
            # for node in self.reverse_dict:
            c = counter([],INF=1, per = 1E4, prefix = behave)
            for node_id,hcount in zip(self.reverse_dict, self.hcounts):
                node = node_dict[node_id]
            # for node,hcount in zip(nodes, self.hcounts):
                obj  = draft_hsummary( node, self.sDB, hcount)
                # if node.id == 285899:
                #     raise Exception(str(hcount))
                if obj:
                    buf.append(obj)
                    c.count()
                if not c.i % 1E4:
        #             hit4cath2cath.objects.bulk_create(buf)
                    callback(buf)
                    buf = []    
            callback(buf)
        c.summary()
        pass
    def Dboth(self, dump = 0):
        self.D_both = wrap_mat(
                wrap_mat(self.D_raw,self.D_norm), self.D_geoavg
            )
        if dump:
            self.dump( name = self.name, attr = 'D_both')
        return self.D_both
        pass
    def clear_MySQL(self,):
        return self.sDB.hit4cath2cath_set.filter(node1__version=self.Cver).delete()
    def to_MySQL(self, bsize = 1E4, ignoreFunc = lambda x: x < 0.0, dry_run = False, cstop = 0):
        reset_database_connection()
        behave = "inserting ISS hits between S35 "
        # cutoff = 0.0

        ###################################################
        ##### Inserting S35-S35 ISS-hit ###################
        ###################################################
        ###################################################

        if isinstance(self.D_both, type(None) ):
            self.Dboth()
                
        it0 = self.D_both.todok().iteritems()
        dct_nodes = self.reverse_dict
        # D_curr = D_norm.todok()

        ##############################################
        ##### This need to be set manually ##########
        ############################################
        # dct_nodes = dict(HMMprofile.objects.values_list('id','cath_node'))
        # cutoff = 0.5


        c = counter([],INF=1, per = bsize, prefix = behave)


        def callback( buf, dry_run = dry_run):
            if not dry_run:               
                hit4cath2cath.objects.bulk_create(buf)

        with transaction.atomic():
            buf = []

            for (x,y),vs in it0:
                c.count()

                v1,v2 = vs
                if len(v1) == 2:
                    v3 = v2
                    (v1,v2) = v1
                else:
                    v3 = 0

                if ignoreFunc(v2):
                # if v2 < cutoff :
                    continue
                node1 = dct_nodes[x]
                node2 = dct_nodes[y]
                nodes = sorted([node1,node2])
        #         hmm1 = (nodes[0])
        #         assert nodes[0]
                jdict = {
                    'node1_id': nodes[0],
                    'node2_id': nodes[1],
                    'ISS_raw': v1,
                    'ISS_norm':v2,
                    'hcount_geoavg':v3,
                    'seqDB_id': self.sDB_id,
                    # 'seqDB': self.sDB,
                    
                }

                obj = hit4cath2cath(**jdict)
                buf.append(obj)

                if not c.i % bsize :
                    # hit4cath2cath.objects.bulk_create(buf)
                    callback(buf)
                    buf = []
                if c.i == cstop:
                    break
            # hit4cath2cath.objects.bulk_create(buf)
            callback(buf)
            buf = []
        c.summary()
    def hitcount(self, **kwargs):
    #     if not kwargs:
    #         kwargs = {"ISS_norm__gte":0.5}
        if self.sDB.name != 'crosshit':
                kwargs.update({
                 'ISS_norm__gte' : 0.5,
                 'ISS_raw__gte' : 10,        
                })
        print self.rfield
        self.mapper = {}
        self.mapper['node2hitseq'] = self.rfield
        self.mapper['node2hit'] = self.rfield.replace('__hits','__hit4hmm2hsp')
        self.mapper['node2sDB'] = self.rfield + '__seqDB'
        self.mapper['node2hmmnode2'] = self.rfield.rstrip('__hmmprofile__hits')
        self.mapper['hmmnode2node'] = self.field.replace('cath_node__','')
    #     self.mapper['node'] = 
    #     self.node2hitseq_field = self.rfield
    #     self.node2hit_field = 
    #     self.seq_field = self.rfield
        self.crosshits = self.sDB.hit4cath2cath_set.filter(
            Q(node1__in=self.hmmnodes)|Q(node2__in=self.hmmnodes)
        )
        qset  = self.crosshits.values_list(
        'node1__'+self.mapper['hmmnode2node'],
        'node2__'+self.mapper['hmmnode2node'],
        )
        for k,v in kwargs.items():
            qset = qset.filter(**{k:v})


        qset = list(qset)
        #### OLD
        # lst = (tuple(sorted([self.forward_dict[e] for e in x])) for x in qset)
        # m = matrify(lst, l = self.l )


        #### NEW
        it = list(qset)
        count = collections.Counter(it)
        d = {}
        for k,v in count.iteritems():
            d[ tuple(self.forward_dict[e] for e in k) ] = (v,)
        l = self.l
        m = dok_matrix( ( l + 1, l + 1 ), dtype = np.int)
        m.update( d )
        return m    

    def MySQL_hitPR( self, bsize = 1E4):
        hmm2cath = dict(self.hmms.values_list('id',self.field))
        DB_hits = hit4hmm2hsp.objects.filter(target__seqDB=self.sDB)
        vals = list(DB_hits.values())
        for x in vals:
            x['node_id']=hmm2cath[x['query_id']]
        vals = sorted(vals,key = lambda x: [x['target_id'], x['node_id']])
        it = itertools.groupby(vals,key = lambda x:x['target_id'])
        it = itertools.chain(*[itertools.combinations(y,2) for x,y in it])

        def pair__hit4hmm2hspDict( lst ):
            hit1,hit2 = lst
            if hit1['node_id'] == hit2['node_id']:
                return None
            hits = lst
        #     if hit1['id'] > hit2['id']:
        #         hits=[hit2,hit1]
        #     else:
        #         hits=[hit1,hit2]
            geoavg  = ( 
                    (hit2['end'] + 1 - hit2['start']) * 
                    (hit1['end'] + 1 - hit1['start']) 
                    ) **0.5
            overlap = (
            min( hit1['end'], hit2['end']) + 1 -
            max( hit1['start'],hit2['start'])
            )

            jdict = {
                'hit1_id':hits[0]['id'],
                'hit2_id':hits[1]['id'],
                'geoavg' : geoavg,
                'overlap': overlap,
            }
            return jdict
        def callback(buf):
            hit4hmm2hspPR.objects.bulk_create(buf)

        reset_database_connection()
        behave = "inserting hit4hmm2hspPR for CATH nodes "

        try:
    #         test
    #     if 1:    
            with transaction.atomic():
                buf = []
                # for node in self.reverse_dict:
                c = counter([],INF=1, per = bsize, prefix = behave)
                for obj in it:
                    obj = pair__hit4hmm2hspDict(obj)
    #                 c.count()

                    if obj:
                        obj = hit4hmm2hspPR(**
                            obj
                           )
                        buf.append(obj)
                        c.count()
                    if not c.i % bsize:
            #             hit4cath2cath.objects.bulk_create(buf)
                        callback(buf)
                        buf = []    
                    if not (c.i + 1)  % 1E5:
                        pass
    #                     raise Exception()
                callback(buf)
        except Exception as e: 
            print str(e)
            pass
        c.summary()
        pass









def contrast__qset(m, nodes_ids = None, sDBs = None ):
    node_obj = blankobj
    # sDBs = None
#     vals = classification.objects.filter(id__in = nodes_ids).values()
#     objs = [node_obj(**val) for val in vals ]
#     nodes_data = dict(zip(self.reverse_dict,objs))
    
    vals = classification.objects.filter(id__in = nodes_ids).order_by('id')
    objs = vals
    nodes_data = dict(zip(nodes_ids, objs))

    OUTPUT = fake__query_set()
    # for k in m.keys():
    idx = 0
    for k,v in m.iteritems():
        idx += 1
        i,j = [ nodes_ids[x] for x in k ]
        node1 = nodes_data[i]
        node2 = nodes_data[j]
        jdict = { 
            'id':idx,
            # 'id': '%d.%d' % (node1.id,node2.id),
            'node1': node1,
            'node2': node2,
            'val1' : v[0],
            'val2' : v[1],
        #     'basehit' : hit1 or hit2,
                }
        if sDBs:
            jdict.update({
                'sDBs' : sDBs,
                # 'seqDB1':sDB1,
                # 'seqDB1':sDB1,
                })
        OUTPUT.append( PR_obj(**jdict))

    return OUTPUT

def contrast__crosshit(sDB1,sDB2,hmms = None):
    if isinstance(hmms,type(None)):
        hmms  = HMMprofile.objects
    m1 = ctmat( hmms, sDB = sDB1, 
               alias = sDB1.name , letter = 'H')
    m2 = ctmat( hmms, sDB = sDB2, 
               alias = sDB2.name , letter = 'H')    
    ct1 = m1.hitcount()
    ct2 = m2.hitcount()
    ctc = concat_dok([ct1,ct2])
    OUTPUT = contrast__qset( ctc, m1.reverse_dict, sDBs = [sDB1,sDB2])
    return OUTPUT







def import_seqDB(seqDB_curr, INPUT, fmt =None, header2acc = None, **kwargs):
    '''
    Dependent on global variables
    '''
    behave = "import sequence database"

    if "debug" not in locals(): debug = 0
    reset_database_connection()
    from Bio import SeqIO

    p_clean = re.compile('[^-,^\.]')
    oldseqs = seqDB_curr.sequence_set.all()


    from time import time
    t0 = time()
    useFisrt = 1
    failcount = 0

    iterator = SeqIO.parse( INPUT, fmt )
    c = counter(iterator,INF=1,per = 1000)
    iterator = SeqIO.parse( INPUT, fmt )

    with transaction.atomic():
        for obj in iterator:

            acc = header2acc( obj )
            seq = p_clean.sub('',
                              obj._seq.tostring())
            length = len(obj.seq)
            try:
                if acc.islower():
                    raise Exception('accession is all lowercase!')
                jdict = {
                    'acc':acc,
                    'length':length,
                    'seqDB':seqDB_curr,
                }

                seqobjs = oldseqs.filter(**jdict)
                if not seqobjs.exists():
                    seqobj = sequence(**jdict)
                    seqobj.save()
    #                     print "created %s"%jdict['acc']
                elif seqobjs.count() > 1:                   
                    print jdict['acc']
                else:
                    pass

            except Exception as e:
                msg = "%s failed for %s " % (acc, e)
                if debug: print >>sys.__stdout__, msg
                c.fail( msg , acc)
            finally:
                c.count()


    c.summary( behave,INPUT )


from tst.domutil.util import *
def import_hmm(Cver,INPUT, header2acc = None, **kwargs):
    behave = "importing HMM profiles to %s" % (INPUT,Cver )
    nodes = Cver.classification_set
    from time import time
    import re

    p_header = re.compile("NAME.*?\n")

    lst = parse_hmmlib( INPUT )
    c = counter( lst,INF = 1, per = 1000 )
    lst = parse_hmmlib( INPUT )
    failcount = 0

    try:
#     if 1:
        with transaction.atomic():
            for hmm_text in lst:
                c.count()
                header = p_header.findall(hmm_text)[0]
                acc = header2acc(header)
                length = int(p_hmmlen.findall(hmm_text)[0])

    #             acc = next(header_gen)
                try:
    #                 cnode = domain.objects.get(domain_id = acc).classification
                    cnode = nodes.get(domain__domain_id = acc)
                    if hasattr(cnode,'hmmprofile'):
                        pass
                    else:
                        hmm = HMMprofile(
                                    cath_node_id = cnode.id,
                                    text = hmm_text,
                                    length = length
                                    )
                        hmm.save()
                except Exception as e:
                    msg = "failed for %s for Exception:%s" %( acc, e)
                    c.fail( msg, acc )

    except Exception as e:
        print "early stop due to %s" % e
    c.summary( behave,INPUT )




def import_domtbl(INPUT, Cver, sDB):    
    '''
        # INPUT = full('$SEQlib/hmm/domtbl/cath-dataset-nonredundant-S40-v4_0_0_cath-S35-hmm3-v4_0_0.domtbl')
        # f_handles = [f0]
    '''
# if 1:
    ts = []
    # for pcount in [9,10,11,12]:
    pcount = 9

    hmms = HMMprofile.objects.filter(id__in=Cver.classification_set.values_list('hmmprofile'))
    acc2hmm_raw  = dict(hmms.defer('text').values_list("cath_node__domain__domain_id","id"))
    acc2seq_raw =  dict(sDB.sequence_set.filter().values_list('acc','id'))

    def parse_worker(fakefile, q, pxs, fmt = 'hmmsearch3-domtab'):
    # def parse_worker(fakefile, fmt = 'hmmsearch3-domtab'):
        c0,acc2hmm,acc2seq = pxs
        import sys
        print fakefile
    #     print>> sys.__stdout__,'inited'
    #     print >> sys.__stdout__,fakefile.closed
        parser = SearchIO.parse(fakefile, fmt)
        for q_hits in parser:
        #     print q_hits
            acc = p_cathdomain.findall(q_hits.id)[0]

            try:
                c1 = counter([],INF=-1,ifprint = 0 )
                query_id = acc2hmm[ acc ]
                jjdict = {'query_id':query_id,
                        'hits' : [], }
                for hit in q_hits:
                    hsp = hit[0]
                    target_acc = p_cathdomain.findall(hit.id)[0]
                    try:
                        jdict = hsp2jdict( hsp,simple = 1)
                        jdict['query_id'] = query_id
                        jdict['target_id'] = acc2seq[target_acc]
                        jjdict['hits'].append(jdict)
                    except BaseException as e:
                        c1.fail('', target_acc)
                    finally:
                        c1.count()
                if c1.f:
                    c0.fail('%d of %d instances failed for HMM %s \n Most Recent Exception' % (c1.f, c1.f, acc, c1.e ), acc)
                q.put( jjdict )

            except Exception as e:
    #             raise Exception(e)
    #             q.put(e)

                try:
                    c0.fail('%s failed for %s'%(q_hits.id, e), q_hits.id)
                except:
                    pass
            finally:
                c0.count()
        c0.summary()



    def db_listener( hmms, q, ):
    # def db_listener( hmms, ):
        c = counter([],INF=1, )
        hmms = hmms.defer('text')
        with transaction.atomic():
            while 1:

                try:
                    obj = q.get()
                    c.count()
                    if obj=='kill':
                        print obj
                        break
                    else:
                        hmm = hmms.get(id = obj['query_id'])
                        oldhits = list(
                            hmm.hits.values_list('id',flat = True)
                        )
                        bulk = []

                        for jdict in obj['hits']:
                            if jdict['target_id'] in oldhits:
                                continue
                            else:
                                db_hit = hit4hmm2hsp(**jdict)
                                bulk.append( db_hit )
    #                             db_hit.save()
                        hit4hmm2hsp.objects.bulk_create( bulk )
                except BaseException as e:
                    print e
                    c.fail('%s'%e,)
    #                 break
            c.summary()





    import sys
    if 1:
        f_handles = split_file( INPUT,number = pcount - 2)
    #     f_handles = split_file( f0,number = pcount - 2)

        import os
        import multiprocessing as mp
        # from 
        from multiprocessing.managers import BaseManager, SyncManager
        # class MyManager(BaseManager): pass
        class MyManager(SyncManager): pass
        MyManager.register('counter',counter)
        from time import time

        t0 = time()
        if __name__=='__main__':
        #     m = mp.Manager()
            m = MyManager()
            m.start()
        #     raise Exception
            c0 = m.counter([],INF=1, ifprint = 1,
#                           stdout = sys.__stdout__
                          )
            acc2hmm = m.dict(acc2hmm_raw)
            acc2seq = m.dict(acc2seq_raw)
            pxs = [c0,acc2hmm,acc2seq]

            q = m.Queue();          
            if 1:
                pool = mp.Pool( pcount )
        #     with mp.Pool(mp.cpu_count() - 1) as pool:
                watcher  = pool.apply_async(db_listener, args = [hmms, q,])
                jobs = []
                for f_handle in f_handles:
                    print f_handle
#                     job  = mp.Process(target = parse)
                    job  = pool.apply_async(parse_worker, args = (f_handle, q, pxs))
                    jobs.append(job)
        
                for job in jobs:                   
                    job.get()
#                 for i in range(1000):
#                     obj = q.get()
#                     print obj
                
                q.put('kill')
                _ = watcher.get()


            ###### Delete temporary files
            for f in f_handles:
                os.remove(f)
    #         c.summary()

        t = time() - t0
        ts.append(t)
        print pcount, t 
    return pool
    
def reset_nodes(Cver):
    Cver.classification_set.all().delete()
    jdict = {   
        'Class'     : 0,
        'arch'      : 0,
        'level_id'  : 1 ,
        'version_id': Cver.id,
        }
    rootnode = verify_exist_entry( classification, **jdict)
    print rootnode
    class_nodes = [
        {   
        'Class'     : 1,
        'arch'      : 0,
        'level_id'  : 2 ,
        'version_id': Cver.id,
        'parent_id' : rootnode.id,
        },
        {   
        'Class'     : 2,
        'arch'      : 0,
        'level_id'  : 2 ,
        'version_id': Cver.id,
        'parent_id' : rootnode.id,
        },
        {   
        'Class'     : 3,
        'arch'      : 0,
        'level_id'  : 2 ,
        'version_id': Cver.id,
        'parent_id' : rootnode.id,
        },
        {   
        'Class'     : 4,
        'arch'      : 0,
        'level_id'  : 2 ,
        'version_id': Cver.id,
        'parent_id' : rootnode.id,
        },
    ]
    for jdict in class_nodes:
        node = verify_exist_entry( classification, **jdict)
        print node
    print Cver.classification_set.count()    
    # print time() - t0