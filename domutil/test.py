from ..utils import *
def test__raw(D_raw, hmms):
    # next(counts.iteritems()[0]
    # it = counts.iteritems()
    it = using_tocoo_izip(D_raw)
    c = counter([],INF = 1)
    for x,y,v in it:
#         print x,y
        # hmm1 = hmms.get(id = x + 1)
        # hmm2 = hmms.get(id = y + 1)
        hmm1 = hmms.get(id = x )
        hmm2 = hmms.get(id = y )
        hmm1hits = hmm1.hits.values_list('id')
        hmm2hits = hmm2.hits.values_list('id')
        interhits = set(hmm1hits) & set(hmm2hits)
        intercount = len(interhits)
#         print v
#         print intercount
        msg = '[OK] %s against %s overlaps %d, with %d from '%(hmm1,hmm2, intercount, v )
        print msg
        assert v == len(interhits),'[ERROR] %s against %s overlaps %d, while D_raw returns %d '%(hmm1,hmm2, intercount, v )
        c.count()
        if c.i == 5:
            break
            
def test__norm(D_curr, hmms, norm_func = ISS_normalise):
    it = using_tocoo_izip(D_curr)
    c = counter([],INF = 1)
    for x,y,v_act in it:
        # hmm1 = hmms.get(id = x + 1)
        # hmm2 = hmms.get(id = y + 1)
        hmm1 = hmms.get(id = x )
        hmm2 = hmms.get(id = y )
        hmm1hits = hmm1.hits.values_list('id')
        hmm2hits = hmm2.hits.values_list('id')
        interhits = set(hmm1hits) & set(hmm2hits)
        intercount = len(interhits)
        
        v_exp = norm_func( len(hmm1hits), len(hmm2hits), intercount)
#         print v
#         print intercount
        msg = '[OK] %s against %s overlaps:: Expected:%s, Actual:%s'%(hmm1,hmm2, v_exp, v_act )
        print msg
        assert v_exp == v_act,'[ERROR] %s against %s overlaps:: Expected %s, Actual: %s '%(hmm1,hmm2, v_exp, v_act )
        c.count()
        if c.i == 5:
            break