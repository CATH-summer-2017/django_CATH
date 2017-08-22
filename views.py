# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.


from django.http import *
from django.template import loader


from django.db.models import Avg,Count,Q
from .models import *

from CATH_API.lib import *
import urllib
import re
import random


import json
from .utils import *
import sys,os

# import os

import cPickle as pk
# if 'D_raw' not in locals().keys():
#     fname = 'data/ISS_raw'
#     D_raw = pk.load(open(fname, 'rb')).todok()
# if 'D_norm' not in locals().keys():
#     fname = 'data/ISS_norm'
#     D_norm = pk.load(open(fname, 'rb')).todok()

#### Displayed shorthands for any field
field_short = {
	"domain_id_urled":"Domain",
	"superfamily_urled":"Superfamily",
	# "view_chopped":"PDBview",
	"view_chopped":"<img src=\"/static/imgs/rasmol.png\" alt=\"chopped_pdb\">",
	"sf_s35cnt": "Superfamily Size",
	"s35_count": "S35rep_count",
	"classification__version__name":"Version",
	"version__name":"Version",
	"node_stat__Rsq_NBcount_Rcount": "R-Squared (residue)",
	"node_stat__Rsq_NBcount_Acount": "R-Squared (atom)",
	"domain_stat__maha_dist":"outlier_score",
	# "": ,
}

#### Displayed captions for any field
field_readable = {
	"domain_id_urled":  "ID of the chopped domain according to CATH, with a URL linking to the corresponding CATH domain page ",
	"superfamily_urled":"ID of the superfamily to which this domain belongs, with a URL linking to the corresponding Doped_CATH page ", 
	"view_chopped":"A clickable button that toggles the embedded PDB viewer",
	"sf_s35cnt": "Number of S35rep in this superfamily",
	"s35_count": "Number of S35rep in this superfamily",
	"residue_count":"Total number of amino acid residues in the PDB structure for this chopped domain ",
	"atom_count":"Total number of atoms in the PDB structure for this chopped domain ",
	"nbpair_count":"Total number of non-bonded interaction pairs (of atoms) in the PDB structure for this chopped domain <br/><br/> The higher this number, the more packed is the structure.",
	"classification__version__name":"The version of CATH at which this domain is assigned",
	"version__name":"The version of CATH at which this superfamily is created",
	"domain_stat__maha_dist":" We detect outliers using the Mahalanobis distance. This metric measures how likely the packing status of a domain is different to its siblings. <br/><br/>  The higher the distance, the more likely this is an outlier. It is also the distance from the origin to any point on the normalised scatter plot",
	###superfamily page
	"node_stat__Rsq_NBcount_Acount":" R-squared of the (atom_count, nbpair_count) bivariate distribution <br/><br/> The lower this value, the less correlated are the variables, potentially due to outliers (within the superfamily) <br/><br/>  R-squared: Squared PPMCC correlation coefficient (R), describe the strength of correlation between two variables  <br/><br/> This statistics is preferred because non-bonded pair is defined to be atom-wise",
	"node_stat__Rsq_NBcount_Rcount":" R-squared of the (residue_count, nbpair_count) bivariate distribution <br/><br/> The lower this value, the less correlated are the variables, potentially due to outliers (within the superfamily) <br/><br/> R-squared: Squared PPMCC correlation coefficient (R), describe the strength of correlation between two variables <br/><br/>",

}

#### Captions for pages
page_captions = {
"domain":'''
	1. This page displays a collection of chopped domains from CATH. 
	<br/>2. You can either browse the data by row, or open up the scatter plot by clicking \"view scatter plot\". 
	<br/>3. You can highlight any row by clicking it. 
	<br/>4. You can view any structure by clicking the Rasmol icon. 
	<br/>5. Blue text are clickable and redirect to either CATH or Doped_CATH 
	<br/>6. Check "Table Legend Table" if you are confused by any column heading"
	''',
"superfamily":'''
	1. This page displays a collection of superfamilies from CATH. They are labeled according to the packedness of their domains 
	<br/>2. You can either browse the data by row, or open up the scatter plot by clicking \"view scatter plot\". 
	<br/>3. You can highlight any row by clicking it. 
	<br/>4. You CANNOT view any structure by clicking the non-existing Rasmol icon. 
	<br/>5. Blue text are clickable and redirect to either CATH or Doped_CATH 
	<br/>6. Check "Table Legend Table" if you are confused by any column heading"
	 ''',
	} 
greet_plothowto = '''
		<br/><br/> How to: 
		<br/>Note this plot is desgined to be interactive. You can:
		<br/>1. Click any point to jump to and highlight the corresponding table row.
		<br/>2. Use the bottom left panel: 
		<br/>&nbsp; to reset your view, 
		<br/>&nbsp; to pan, 
		<br/>&nbsp; to box-zoom, 
		<br/>&nbsp; to fit to content, respectively.
'''
greets = {
	"scatterplot_domain":[
		'Unnormalised scatter plot <br/>You are looking at a collection of domain structures',

		'''This is a scatter plot showing the distribution of packedness within a superfamily, using un-normalised metrics. Each point represent a domain structure. 
		<br/><br/>x-axis: atom_count, the number of atoms contained in this domain structure
		<br/><br/>y-axis: nbpair_count, a geometric measurement of the structure's packedness. The higher the number, the more packed the structure, vice versa.
		%s
		'''%greet_plothowto,
		],
	"scatterplot_homsf":[
	'Normalised scatterplot <br/> You are looking at a collcetion of homologous superfamilies',

	'''This is a scatter plot showing the homogeneity of superfamilies using correlation coefficient (R) at s35 level. The more s35 contained, the more constrained is the R, and hence the higher the R-sqaured, as a result of central limit theorem. Each point represent a homologous superfamily. 
		<br/><br/>x-axis: pcx (relative structure size), the number of s35 rep's contained in this superfamily
		<br/><br/>y-axis: R-squared, the rating of homogeneity. The higher the R-sqaured, the more homogeneous is the superfamily. However, note that this does not reflect the homogeneity in terms of structure size, but only that all structures fold into similar packing status. 
		<br/><br/>Also note that R-sqaured is expected to increase on removal of outliers.
		%s
		'''%greet_plothowto],
	"scatterplot_maha":[
	'Normalised scatterplot <br/>You are looking at a collcetion of domain structures',

	'''This is a scatter plot showing the distribution of packedness and relative structure size across all superfamilies in CATH, using PCAed and normalised metrics. Each point represent a domain structure. 

		<br/><br/>Normalisation: The raw distribution are rotated and decorrelated with PCA and then normalised at superfamily level, and superimposed. For small/messy superfamily, the two axes may be swaped for there is no robust observable trend in packing status.

		<br/><br/>x-axis: pcx (relateive structure size): The size of a domain structure relative to its siblings within the same homolgous superfamily. Large domains indicate potential emblishments, or consecutive domains incorrectly merged.
		<br/><br/>y-axis: pcy (packedness): The packedness of a domain structure relative to its siblings. Postive means more packed structure, whereas negative means less packed, when compared to its siblings.
		<br/><br/> Note this plot may be filtered using Mahalanobis distance (distance from the origin), producing a central hole. The centre is supposedly occupied by the most canonical sturctures of any single superfamily, thus unlikely to be an outlier. 
		%s
		'''%greet_plothowto],
}



from django.db.models import F
###### Prefiltering
CCXhit = hit4cath2cath.objects.exclude(node1__parent=F("node2__parent") ) 

def index(request):

	output = 'index is now empty'
	page_caption  = "Nothing"
	context = {
		'query_set':[],
		'tst_a':0,	
		's35cnts':[],
		'field_names':[],
		'title':"homepage",
		'field_readable':field_readable,
		'field_short':field_short,
		'page_caption': page_caption,
		}	
	return render(
		request,
		"tst/index.html",
		context,
		)

def test(request):
	return HttpResponse("this is a test page")

def redirect(request, url):
	# abs_url = request.path ### this is temporary

	abs_url = request.path.rstrip('/') ### this is temporary
	# abs_url = request.path.rstrip('/') + url ### this is temporary
	
	# output = 'index is now empty'
	# return HttpResponse('This page should redirect you to %s'%(abs_url))
	return HttpResponseRedirect(abs_url)
	# output = ',<br/> '.join([q.question_text for q in latest_question_list])
	# return HttpResponse("Hello, world. You're at the polls index.")
	# return HttpResponse( '<!DOCTYPE HTML><html>' + ' The output is: <br/>'+ output+'</html>')

####
def domain_detail(request, domain_id):
	return HttpResponse("You're viewing detail page on CATH domian %s." % domain_id)

def view3d(request):
	did = "2c7wA00";
	did = "1fzpD00";
	context={ "d" :domain.objects.get(domain_id=did)};
	return render(request,
			 'tst/3dviewer.html',
			  context)




#### Common function to render a table view

def view_qset(request, query_set, orders = None, cols = None,title = None,page_caption = None ):
###################################################################################
###################################################################################
## Arguments: 1. request: the HTTP request to be rendered #########################
##############2. query_set: The Django QuerySet instance to be tabulated ##########
##############3. orders (optional) :  How should the query_set be ordered #########
##############4. cols (necessary)  :  A list of attributes of an element from #####
##############   query_set be rendered    #########################################
##############5. title: Title of the returned HTML page ###########################
###################################################################################

	# sf_list = CATH_superfamily('v4_1_0')[1]
	if hasattr(query_set,'model'):
		if query_set.model == domain:
			query_set = query_set.annotate(sf_s35cnt=Count('classification__parent__classification'))	
			# orders = orders or ['-sf_s35cnt','-nDOPE'];
			cols=cols or [
			'domain_id_urled',
			'superfamily_urled',
			'view_chopped',
			'sf_s35cnt',
			'residue_count',
			'atom_count',
			# 'nDOPE',
			'nbpair_count',
			'domain_stat__maha_dist',
			'classification__version__name',];
			title = title or "domain collection" 
			page_caption = page_captions["domain"]
		if query_set.model == classification:
			# query_set = query_set.annotate(sf_s35cnt=Count('classification__parent__classification'))	
			# orders = orders or ['-s35_count','-nDOPE_avg'];
			# query_set = query_set.order_by(*orders)
			# cols=cols or ['superfamily','s35_count','rep_s35','domain_length','nDOPE'];

			cols=cols or [
			'superfamily_urled',
			's35_count',
			's35_len_avg',
			'nDOPE_avg',
			'nDOPE_std'];
			title = title or "superfamily collection"
			page_caption = page_captions["superfamily"]
	else: 
		pass

	if orders:
		query_set = query_set.order_by(*orders)
	if "page_caption" not in locals().keys():
		page_caption = "No caption is provided for this page"

	context = {
		'query_set':query_set,
		'tst_a':0,	
		's35cnts':[],
		'field_names':cols,
		'title':title,
		'field_readable':field_readable,
		'field_short':field_short,
		'page_caption': page_caption,
		}
	return render(request,
				 # 'tst/index.html',
				 'tst/view_table.html',
				  context)
forward_field = {
    'S':'cath_node__id',
    'H':'cath_node__parent__id',
    'T':'cath_node__parent__parent__id',
    'A':'cath_node__parent__parent__parent__id',
    'C':'cath_node__parent__parent__parent__parent__id',
}

reverse_field = {
    'S':'hmmprofile__hits',
    'H':'classification__hmmprofile__hits',
    'T':'classification__classification__hmmprofile__hits',
    'A':'classification__classification__classification__hmmprofile__hits',
    'C':'classification__classification__classification__classification__hmmprofile__hits'
}

def tab__CCXhit__S35(request,qset,**kwargs):
	cols = ['node1',
	# 'node1__id','node2__id',
	'node2','xhit_urled',
	 # 'node1__hitCount',
	'compare_hitlist',
	  # 'node2_hitCount', 
	  'node1__hmmprofile__hits__count',
	  'node2__hmmprofile__hits__count',

	   'ISS_raw', 'ISS_norm']
	title = 'ISS_test'
	# orders = []
	response = view_qset(
		request,
		qset, 
		cols = cols,
		title = title,
		**kwargs
		)
	return response 


def cross_qset(node1__id,node2__id):
	node1 = classification.objects.get(id = node1__id)
	node2 = classification.objects.get(id = node2__id)
	s35_1 = node1.classification_set.all()
	s35_2 = node2.classification_set.all()
	hits_id1A = set(s35_1.values_list("node1",flat = True) )
	hits_id1B = set(s35_1.values_list("node2",flat = True) )
	hits_id2A = set(s35_2.values_list("node1",flat = True) )
	hits_id2B = set(s35_2.values_list("node2",flat = True) )

	hits_ids = ( hits_id1A | hits_id1B)  &  ( hits_id2A | hits_id2B)
	qset =  CCXhit.filter(id__in=hits_ids)
	# raise Exception("here")

	return qset


def test__CCXhit(request):
	# filters = request.GET.get('filters', {"ISS_norm__lte":0.9})

	filters = request.GET or {"ISS_norm__lte":0.9}
	# raise Exception("here")
	kwargs = {}

	if 'node1__id' in filters.keys():
		node1__id =  filters["node1__id"]
		node2__id =  filters["node2__id"]
		node_ids = sorted(
			[int(node1__id),
			int(node2__id)
			])
		
		qset = cross_qset( node_ids[0],node_ids[1])
		# print ""
		# raise Exception("here")

		node1 = classification.objects.get(id = node1__id)
		node2 = classification.objects.get(id = node2__id)


		hit = hit4cath2cath.objects.get(
			node1=node_ids[0],
			node2=node_ids[1])


		kwargs['page_caption'] = '''
		<br/>Node1: %s 
		<br/>Node2: %s
		<br/>ISS_raw:%s
		<br/>ISS_norm%s''' % (node1,node2, hit.ISS_raw, hit.ISS_norm)
	else:
		qset = CCXhit.filter(**filters) 


	# hit4cath2cath.objects.values_list('node1__id'.'node2__id')
	# qset = hit4cath2cath.objects.exclude(node1__parent=F("node2__parent") ) 
	# qset = CCXhit.exclude(ISS_norm__gte=0.9) 

	# qset = CCXhit.filter(ISS_norm__lte=0.9) 

	qset = qset.order_by('-ISS_norm')
	qset = qset[:500]
	# .prefetch_related(["node1__hmmprofile","node2__hmmprofile"])
	# qset = qset.annotate(
	# 	# node1_hitCount = Count("node1__hmmprofile__hits"), 
	# 	# node2_hitCount = Count("node2__hmmprofile__hits"),
	# 		)
	return tab__CCXhit__S35(request,qset, **kwargs)

def test__hmm_compare(request,hmm1__id = None,hmm2__id = None):
	# params = request.GET or {"hmm1__id":17150,"hmm2__id":4067}
	hmm1__id = request.GET.get("hmm1__id",'17150')
	hmm2__id = request.GET.get("hmm2__id",'4067')

	hmm1 = HMMprofile.objects.get(id = hmm1__id)
	hmm2 = HMMprofile.objects.get(id = hmm2__id)
	# interhit = 
	hitlist1 = hmm1.hit4hmm2hsp_set
	hitlist2 = hmm2.hit4hmm2hsp_set
	# raise Exception()

	return hitlist_compare(request, hitlist1,hitlist2)
	# pass

class blankobj():
	def __init__(self,**kwargs):
		for k,v in kwargs.iteritems():
			setattr(self,k,v)
		pass

def hitlist_compare(request,hitlist1,hitlist2):
	hits1_ids = hitlist1.values_list('target',flat = True)
	hits2_ids = hitlist2.values_list('target',flat = True)
	inter_ids = set( hits1_ids ) & set( hits2_ids )
	lst = zip( 
		hitlist1.filter(target__in = inter_ids).order_by("target"),
		hitlist2.filter(target__in = inter_ids).order_by("target"),
		)
	qset = [blankobj(id=i,hit1=x,hit2=y) for i,(x,y) in enumerate(lst)]
	# for x,y

	cols = [
	'hit1__target__acc',
	'hit1__target__GETcath_node',
	'hit1__start',
	'hit1__end',
	'hit2__end',
	'hit2__start',
	'hit1__bitscore',
	'hit2__bitscore',

	]

	title = 'ISS_hitlists'

	response = view_qset(
		request,
		qset, 
		cols = cols,
		title = title,
		)
	return response


def test__CCXhit_homsf(request):
	# hit4cath2cath.objects.values_list('node1__id'.'node2__id')
	# qset = hit4cath2cath.objects.exclude(node1__parent=F("node2__parent") ) 
	# qset = CCXhit.exclude(ISS_norm__gte=0.9) 
	letter = 'H'
	rv_field = reverse_field[letter]
	qset = CCXhit.filter(node1__level__letter='H') 
	qset = qset.order_by('-ISS_norm')
	qset = qset.exclude(ISS_norm__gte=0.7)

	qset = qset[:1000]
	# .prefetch_related(["node1__hmmprofile","node2__hmmprofile"])
	# qset = qset.annotate(
	# 	# node1_hitCount = Count("node1__hmmprofile__hits"), 
	# 	# node2_hitCount = Count("node2__hmmprofile__hits"),
	# 		)

	cols = ['node1',
	# 'node1__id','node2__id',
	'node2','xhit_urled',
	'local_CCXhit',
	'node1__hitCount',
	'node2__hitCount', 
	  # 'node1__%s__count' % rv_field,
	  # 'node2__%s__count' % rv_field,

	   'ISS_raw', 'ISS_norm']
	title = 'ISS_test'
	# orders = []
	response = view_qset(
		request,
		qset, 
		cols = cols,
		title = title,
		)
	return response 

### Visualise a collection of domain_id's

# def domain_collection(request):
# 	# latest_question_list = Question.objects.order_by('-pub_date')[:5]
# 	dquery = request.GET.get('dquery', [])

# 	if dquery:
# 		dquery = re.sub('[^A-Za-z0-9\_]+', '', dquery).split('_');
# 		# domain_list = domain.objects.filter(domain_id__in=dquery)
# 		domain_list = domain.objects.none();
# 		for q in dquery:
# 			if q:
# 				domain_list = domain_list | domain.objects.filter(domain_id__startswith=q[:4]); 
# 	else:
# 		# domain_list = domain.objects.filter(nDOPE__gte=1.5)
# 		qset = domain.objects.order_by('-domain_stat__maha_dist')[:1000]
# 		domain_list = qset
# 	# orders = ['-sf_s35cnt','-nDOPE']
# 	orders = []

# 	# orders = 
# 	return view_qset(request,domain_list,orders)


# url = reverse('fig_nbscatter',args=[homsf_id])
		

#### Visualise a collection of superfamilies

def homsf_collection(request, homsf_id = None,
	crit = {'s35_count__gt':10,},
	):
	if not homsf_id:
		### filter for the superfamily/ index page
		# homsf_list = (classification.homsf_objects.filter(nDOPE_avg__gte=1.0 ) | 
		# 	classification.homsf_objects.filter(nDOPE_std__gte = 0.1 ))
		homsf_list = classification.homsf_objects.filter(**crit)
		# homsf_list = classification.homsf_objects.filter(s35_count__lte=100).filter(s35_count__gte=10)

		return view_qset(request,homsf_list,
				# orders = ['-nDOPE_std'],
				orders = ['node_stat__Rsq_NBcount_Acount'],

				# cols = ['superfamily_urled','s35_count','s35_len_avg','nDOPE_avg','nDOPE_std'],
				cols = ['superfamily_urled','s35_count',
					'node_stat__Rsq_NBcount_Rcount',
					'node_stat__Rsq_NBcount_Acount',
					'version__name',
					# 's35_len_avg','nDOPE_avg','nDOPE_std',
					],				
				)
	else:
		pass


def homsf2domain(homsf_id):
	if not homsf_id:
		qset = classification.objects.filter(level__letter='S')
		# qset = domain.objects.filter(classification__in=homsf.classification_set.all())
		qset = qset.order_by('-domain__domain_stat__maha_dist')[:500]#
		qset = domain.objects.filter(classification__in=list(qset))
		qset = qset.order_by('-domain_stat__maha_dist')[:500]#
		# qsetlst = (n.domain for n in qset)
		# qset = reduce(lambda x, y: x | y, qsetlst, domain.objects.none())
		# qset = domain.objects.filter(classification__in=qset.classification_set.all())

	else:
		homsf = classification.objects.get_bytree( homsf_id )[0]
		qset = domain.objects.filter(classification__in=homsf.classification_set.all())
		# domain_list = domain_list.order_by('-nDOPE')

		qset = qset.order_by('-domain_stat__maha_dist')
	return qset

def domain_collection(request, homsf_id = None,
	# crit = {'s35_count__gt':10,},
	):
	'''
	specifying qset		
	'''
	qset = homsf2domain(homsf_id)
	# cols = ['domain_id','superfamily_urled','sf_s35cnt','domain_length','nDOPE'];
	cols = [];
	return view_qset(
		request,
		qset,
		cols=cols,
		title = "s35reps from %s" % (homsf_id) 
							)

###  !!!!!!!!!!!!!!!!!!!! Deprecated
def scatterplot_qset(request,homsf_id='1.10.30.10'):
	# jdict, errmsg = scatterplot_json(homsf_id)
	# # jdict = scatter_plot(xs,ys)
	# jdict['success'] = True
	# jdict['errmsg'] = 'Successful'

	# try:
	if 1:
		# jdict = scatterplot_json(homsf_id)
		jdict = scatterplot_homsf_dict(homsf_id)
		jdict['success'] = True
		jdict['errmsg'] = 'Successful'
	# except Exception as e:
	# 	exc_type, exc_obj, exc_tb = sys.exc_info()
	# 	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	# 	errmsg = ' '.join([str(x) for x in [exc_type, fname,' line ', exc_tb.tb_lineno,': ', str(e)]]).replace("'",'_')
	# 	jdict = {'success': False,
	# 			'errmsg': errmsg};

	# finally:
	
	jstr = json.dumps(jdict).replace('\\n','').replace("'",'"');
	context = {
	'query_set': [],
	'title': 'superfamily %s'%homsf_id,
	'fig_json1': jstr,
	}
	# print(jstr) ## just for debugging the JSON issue
	return render(request,
			 'tst/nbscatter_template.html',
			  context)


	

def scatterplot_qset( request, qset = None, title = None, fields = None, greet = None, filter = [], **kwargs):
	# title = 
	# title = 'No_title' if 'title' not in kwargs else title
	# greet = 'No greeting was provided' if not 'greet' in kwargs else greet
	# print title
	# print '\n'
	# jdict = scatterplot_homsf_dict(qset,fields = fields, **kwargs)
	# print kwargs.get('greet')
	# print(subplot_kwargs,'\n\n')
	fields_t = request.GET.get('FigFields','+'.join(fields))
	# filter = request.GET.get('FigFilter','+'.join(filter)).split('+')
	# print(fields_t)
	# print(kwargs.has_key('subplot_kwargs'))
	# labels = list(qset.values_list('domain__domain_id',flat=True))
	# print kwargs.keys()
	jdict = scatterplot_qset_dict(qset.filter(*filter), fields = fields, **kwargs)
	jdict['success'] = True
	jdict['errmsg'] = 'Successful'

	jstr = json.dumps(jdict).replace('\\n','').replace("'",'"');
	
	context = {

	'query_set': [],
	'title': title,
	'greet': greet ,
	# 'greet': fields_t ,

	'fig_json1': jstr,
	}
	

	return render(request,
			 'tst/nbscatter_template.html',
			  context)


def scatterplot_domain(request,
	# homsf_id='1.10.30.10',
	homsf_id=None):
	# homsf = select_homsf(homsf_id)
	# qset = homsf.classification_set.all()
	scatter = request.GET.get('scatter','raw')

	qset = homsf2domain(homsf_id)
	try:
		qset = qset.exclude(domain_stat__isnull = True) ##### IMP!! This is incompatible with the slicing , need to implement slicing afterwards
	except Exception as e:
		print e


	if scatter == 'raw':
		fields  = [
			# 'domain__domain_stat__res_count',
			'domain_stat__atom_count',
			'domain_stat__nbpair_count',
			'id',
			# 'domain_id',
			]

		greet = greets["scatterplot_domain"][:]
		greet[0] += " from %s" % homsf_id 
		kwargs = 	{
		'title': 'superfamily %s' % homsf_id,
		# 'greet': 'You are looking at a collection of s35_reps ',
		# 'greet': greets["scatterplot_domain"],
		"greet": greet,
		'subplot_kwargs':{
			# 'xlim':[0,500],
			'xlim':[0,500E1],
			'ylim':[0,800E3],
			'xlabel':'atom_count',
			'ylabel':'Non-bonding pair count',
			},
		"labels":list(qset.values_list('domain_id',flat=True)),
		"fields":fields,
		}
	elif scatter == 'pcnorm':
		fields = [
			'domain_stat__pcx',
			'domain_stat__pcy',
			'id',
			]

		kwargs = 	{
		'title': 'All domains',
		'greet': greets["scatterplot_maha"],
	
		'subplot_kwargs':{
			'xlim':[-5,10],
			'ylim':[-9,7],
			'xlabel': 'pcx (relative structure size)',
			'ylabel': 'pcy (packedness)',
			"regress":False,
			},

		"labels":list(qset.values_list('domain_id',flat=True)),
		"fields":fields,
		}

	return scatterplot_qset(
		request,
		qset,
		# fields = fields,
		# title = 'superfamily %s' % homsf_id,
			# labels = qset.values_list('domain__domain_id',flat=True),
		**kwargs)

def scatterplot_homsf(request, 
	crit = {'s35_count__gt':10,}
	):
	# homsf = select_homsf(homsf_id)
	# qset = homsf.classification_set
	# crit = 
	qset =  classification.homsf_objects.filter( **crit )

	fields  = [
		# 'domain__domain_stat__res_count',
		's35_count',
		'node_stat__Rsq_NBcount_Acount',
		'id',
		# 'superfamily',
		]

	kwargs = 	{
	'title': 'superfamily collection' ,
	'greet': greets["scatterplot_homsf"],
	# 'You are looking at a collection of %s'%qset[0].level.name,	
	'subplot_kwargs':{
		# 'xlim':[0,500],
		# 'xlim':[0,500E1],
		# 'ylim':[0,800E3],
		'xlabel':'s35 Count',
		# 'ylabel':'Rsq_NBcount_Acount',
		'ylabel':field_short['node_stat__Rsq_NBcount_Acount'],
		'regress':False,
		},
	'labels': [q.superfamily() for q in qset],
	}

	return scatterplot_qset(
		request,
		qset,
		fields = fields,
		# title = 'superfamily %s' % homsf_id,
		**kwargs
		)



def scatterplot_domain_maha(request):
	# dset=domain
	# qset = domain.objects.all()#
	# qset = domain.objects.order_by('-domain_stat__maha_dist')[:1000]#
	qset = classification.objects.exclude(domain__domain_stat__isnull = True)
	qset = qset.order_by('-domain__domain_stat__maha_dist')[:1000]#
	# qset = classification.objects.order_by('-domain__domain_stat__maha_dist')[:1000]#

	# fields = [
	# 	# 'classification__parent__node_stat__Rsq_NBcount_Acount',
	# 	# 'domain_stat__maha_dist',
	# 	# 'classification__parent__node_stat__Rsq_NBcount_Acount',
	# 	'domain_stat__pcx',
	# 	'domain_stat__pcy',
	# 	'id',
	# 	]
	fields = [
		# 'classification__parent__node_stat__Rsq_NBcount_Acount',
		# 'domain_stat__maha_dist',
		# 'classification__parent__node_stat__Rsq_NBcount_Acount',
		'domain__domain_stat__pcx',
		'domain__domain_stat__pcy',
		'domain__id',
		]
	# (xs,ys,lbls) = zip(*sset.values_list(
	# 	'classification__parent__node_stat__Rsq_NBcount_Acount',
	# 	'domain_stat__maha_dist',
	# 	'id'))
	# jdict = scatterplot_qset_dict(qset.filter(*filter), fields = fields, **kwargs)
	# jdict = scatterplot_dict(xs,ys,lbls, regress = 0)



	kwargs = 	{
	'title': 'All domains',
	# 'greet': 'You are looking at a collection of s35_reps ',
	'greet': greets["scatterplot_maha"],
	# 'You are looking at a collection of %s' % 'domains',	

	'subplot_kwargs':{
		# 'xlim':[0,500],
		# 'xlim':[0,500E1],
		# 'ylim':[0,800E3],
		'xlabel': 'pcx (relative structure size)',
		'ylabel': 'pcy (packedness)',
		# 'xlabel':'atom_count',
		# 'ylabel':'Non-bonding pair count',
		"regress":False,
		},
	"labels":list(qset.values_list('domain__domain_id',flat=True)),
	"fields":fields,
	}

	return scatterplot_qset(
		request,
		qset,
		# fields = fields,
		# title = 'superfamily %s' % homsf_id,
			# labels = qset.values_list('domain__domain_id',flat=True),
		**kwargs)

def scatterplotter(request):
	params = request.GET
