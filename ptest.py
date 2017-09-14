##########
## test ##
##########


from tst.domutil.util import *



# def assert_expr(act, expr, behave = None, **kwargs):
# #     expr0 = expr[:]
#     fullexpr = ' act ' + expr
#     basemsg = "Expecting:%s, Actual:%s " % (expr,act)
#     success = eval(fullexpr,locals(),kwargs)
#     assert( success ),"[FAILED]:" + basemsg
#     print "[PASSED]:" + basemsg


def test__hitlist_compare():

    def init_data():
        node1 = classification.objects.get(id=309877) ### supfam:3.30.9.10.0
        node2 = classification.objects.get(id=310384) ### supfam:3.40.50.20.0
        sDB = seqDB.objects.get(name = 'CATH')
        exp = 68
        return( {'node1':node1,'node2':node2,'sDB':sDB, 'exp':exp})

#     locals().update(init_data())
    func_name = 'hitlist_compare'
    # func = eval(func_name,)
    func = eval(func_name)
    
    print "[testing '%s']" %func_name
    data = init_data()
        
    hitPlist = func( data["node1"].id, data["node2"].id, data["sDB"] )

    
    behave = "Testing length of output list"
    exp = data["exp"]
    assert_expr( len(hitPlist), " == exp ", **data )
#     assert act == data["exp"],'[failed] %s exp:%s, act:%s ' 