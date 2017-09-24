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
def parse_domain(line, v = verify_version('test') ):
#     global cc
#     ### verify version
#     ver = 'putative'
#     v = verify_version(ver)
    
    lst = line.split()
    domain_id = lst[0]
    homsf_str = lst[1]    
    chopping = lst[2]
    

    #### Check whether this node exists in 'classification' table
#     (node,success) = classification.objects.get_bytree(node_str)
    (node,success) = classification.objects.get_bytree(homsf_str)
    
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
    def __init__(self, hmms, sDB = None, seqs = None, letter = None, 
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
        self.reverse_dict = sorted(set( self.hmms.values_list( self.field, flat = True)))
        self.forward_dict = list2dict( self.reverse_dict )
        self.l = len(self.reverse_dict)
        self.hits = self.seqs.filter(**{"hit4hmm2hsp__query__%s__in" % self.field : self.reverse_dict })
        self.nodes = classification.objects.filter(id__in=self.reverse_dict)

    
    def OOLD_hit_sum(self,):
        all_nodes = classification.objects.filter(version__name='v4_1_0')
        curr_nodes = all_nodes.filter(level__letter = self.letter).defer(self.rfield.replace("__hits","__text"))
        
        #   %%time
        ########################################################
        ###### Slightly faster    ####################
        ########################################################
        qset = curr_nodes.annotate(
        hcount=Count(Case(
                When(**{
                    self.rfield+"__seqDB":self.sDB,
                    "then":1}),
        #         output_field=CharField(),
            ))
        )
        hcounts = qset.values_list('id','hcount')
        # dict()
        # lst = list(hcounts1)
        d = dict( list(hcounts) )
        hcounts = [ d[x] for x in self.reverse_dict]
        self.hcounts = hcounts
    
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
        return self.sDB.hit4cath2cath_set.delete()
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
    if not hmms:
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