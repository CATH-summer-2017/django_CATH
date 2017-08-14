from .models import *
from domutil.util import *
# from utils import *
import numpy as np 
from django.db import transaction
import os ,sys

from django.conf import settings

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



from copy import copy
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
            
            
            node = copy(node);
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





#### ISS
def seqheader_guess_parser(header):
    if header.startswith('cath') or header.startswith('CATH') :
        header_parser = seqheader_parse_cath
    
    jdict = header_parser(header)
    seqDB_curr = verify_exist_entry( jdict["seqDB"], seqDB)
    
    return( [header_parser, seqDB_curr])


def verify_exist_entry(jdict, dbmodel):
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


