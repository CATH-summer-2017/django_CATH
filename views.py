# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.


from django.http import *
from django.template import loader
from django.views import View

from django.db.models import Avg,Count,Q
from .models import *

from CATH_API.lib import *
import urllib
import re
import random


import json
from .utils import *
import sys,os


import cPickle as pk



from django.views.generic import ListView


from django.urls import reverse
import copy


# class PublisherList(ListView):
#	 model = Publisher


cols = ['superfamily_urled','s35_count',
					'node_stat__Rsq_NBcount_Rcount',
					'node_stat__Rsq_NBcount_Acount',
					'version__name',
					# 's35_len_avg','nDOPE_avg','nDOPE_std',
					],		
					



# import os
class TemplateView(View):
	# self.template = None
	def get(self, request):
		# <view logic>
		return HttpResponse('result')

# if 'D_raw' not in locals().keys():
#	 fname = 'data/ISS_raw'
#	 D_raw = pk.load(open(fname, 'rb')).todok()
# if 'D_norm' not in locals().keys():
#	 fname = 'data/ISS_norm'
#	 D_norm = pk.load(open(fname, 'rb')).todok()

#### Displayed shorthands for any field
field_short = {
	"domain_id_urled":"Domain",
	"superfamily_urled":"Superfamily",
	"node__superfamily_urled":"Superfamily",
	# "view_chopped":"PDBview",
	"view_chopped":"<img src=\"/static/imgs/rasmol.png\" alt=\"chopped_pdb\">",
	"sf_s35cnt": "Superfamily Size",
	"s35_count": "S35rep_count",
	"classification__version__name":"Version",
	"version__name":"Version",
	"node_stat__Rsq_NBcount_Rcount": "R-Squared (residue)",
	"node_stat__Rsq_NBcount_Acount": "R-Squared (atom)",
	"domain_stat__maha_dist":"outlier_score",
	"hcount_geoavg":"average hit count",
	"ISS_raw":"ISS_raw",
	"node1__hit_summary_set__all?__0__hcount":"node1_hcount",
	"node2__hit_summary_set__all?__0__hcount":"node2_hcount",
	# "hit1__bitscore":"hit1__bitscore"
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

	"scatterplot__hit4cath2cath":[
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
# cnodes = classification
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

def view_qset(request, query_set, orders = None, cols = None,title = None,page_caption = None, **kwargs):
###################################################################################
###################################################################################
## Arguments: 1. request: the HTTP request to be rendered #########################
##############2. query_set: The Django QuerySet instance to be tabulated ##########
##############3. orders (optional) :  How should the query_set be ordered #########
##############4. cols (necessary)  :  A list of attributes of an element from #####
##############   query_set be rendered	#########################################
##############5. title: Title of the returned HTML page ###########################
###################################################################################
	# request.session["qset"] = query_set
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

	meta = {
			'title':title,
			'field_readable':field_readable,
			'field_short':field_short,
			'page_caption': page_caption,
			}
	meta.update(kwargs)
	print meta.keys()

	context = {
		'query_set':query_set,
		'field_names':cols,
		'meta': meta
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

def tab__CCXhit__S35(request, qset, **kwargs):
	cols = ['node1',
	# 'node1__id','node2__id',
	'node2','xhit_urled',
	'compare_hitlist',
	 'node1__hit_summary__hcount',
	  'node2__hit_summary__hcount', 
	  'node1__hmmprofile__hits__count',
	  'node2__hmmprofile__hits__count',

	   'ISS_raw', 'ISS_norm']
	title = 'ISS_test'
	# orders = []
	figurl = '/tst/figure' + request.get_full_path()
	button1 = blankobj( 
		url = figurl,
		text = '''[scatter]<br/>
		x: ISS_raw<br/>
		y: average hit ''',
		)

	response = view_qset(
		request,
		qset, 
		cols = cols,
		title = title,
		buttons = [button1],
		**kwargs
		)
	return response 


def test__CCXhit__S35(request):
	# filters = request.GET.get('filters', {"ISS_norm__lte":0.9})
	qset = init__CCXhit__qset(request)
	# .prefetch_related(["node1__hmmprofile","node2__hmmprofile"])
	# qset = qset.annotate(
	# 	# node1_hitCount = Count("node1__hmmprofile__hits"), 
	# 	# node2_hitCount = Count("node2__hmmprofile__hits"),
	# 		)
	return tab__CCXhit__S35(request,qset,)

	
###### IN USE #########
def param2dict(request, key, default = None):
	param_str= request.GET.get(key, default )
	if param_str:
		param_list = param_str.split()
		d = dict(zip( param_list[::2], param_list[1::2]) )
	else:
		d = {}
	return d

def read__seqDB(request, **kwargs):
	kwargs['default'] = kwargs.get('default', "name CATH-S40-nr version 4_1_0")
	d = param2dict(request, 'seqDB',**kwargs)
	return d
def read__filter(request, **kwargs):
	d = param2dict(request, 'filter', **kwargs)
	return d
def init__hitlistPR(request):
	node1__id = request.GET.get("node1__id",'309754')
	node2__id = request.GET.get("node2__id",'310524')
	
	crit = {
	"stat__gte":0.4,
	"masked__isnull":0,
	}
	crit.update(read__filter(request))
	
	sDB_dict  = read__seqDB(request)
	sDB = seqDB.objects.get(**sDB_dict)

	qset = hitlist_compare(
		node1__id,
		node2__id, 
		sDB )
	qset = qset.filter(**crit)

	node__ids = sorted([node1__id,node2__id])
	try:
		parent = hit4cath2cath.objects.get(node1 = node__ids[0], node2 = node__ids[1], seqDB = sDB)
		parent.ISS_raw = qset.count()
		parent.update__ISS_norm()
	except Exception as e:
		# parent = None
		parent = e

	return qset,parent
	# return ( [ qset, parent])
def tab__hitlistPR(request, ):

	qset,parent = init__hitlistPR(request)
	# raise Exception('/tst/figure' + request.get_full_path())


	cols = [
	# 'id',
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
	
	figurl = '/tst/figure' + request.get_full_path()
	buttons = []
	buttons +=[ blankobj( 
	# url = reverse(scatterplot_domain,args=[x for x in [homsf_id] if x]),
	url = figurl,
	text = '''[scatter]<br/>
	x: hit1__bitscore<br/>
	y: hit2__bitscore''',
	)
	]

	# request
	fakereq = copy.copy(request)
	# if not fakereq.GET._mutable:
	# 	fakereq.GET._mutable = True
	# fakereq.GET = fakereq.GET
	Gdict = request.GET.copy()
	Gdict['fields'] =  ' '.join(['geoavg','overlap','id'])
	# fakereq._load_post_and_files()

	# raise Exception(fakereq.get_full_path())
	# raise Exception(fakereq.GET)
	# request.GET.update({'fields': ' '.join(['geoavg','overlap','id'])} )
	buttons +=[ blankobj( 
	# url = reverse(scatterplot_domain,args=[x for x in [homsf_id] if x]),
	url = '/tst/figure%s?%s' % ( fakereq.path , Gdict.urlencode() ),
	text = '''[scatter]<br/>
	x: average hit span<br/>
	y: overlap hit span''',
	)
	]


	response = view_qset(
		request,
		qset, 
		cols = cols,
		title = title,
		parent = parent,
		buttons = buttons,
		)
	return response



# dict_hit2tid = dict(hit4hmm2hsp.objects.values_list('id','target__id'))

# def hitlist_compare(request, node1__id = None, node2__id = None, sDB = None, **kwargs):
def init__CCXhit_homsf(request = None):
	# letter = 'H'
	# rv_field = reverse_field[letter]
	crit = {
	# 'node1__level__letter':'H',
	'ISS_norm__lte':0.7,
	'ISS_raw__gte':10,
	}
	limit = 1000
	order = ['-ISS_norm']

	if request:
		sDB_dict  = read__seqDB(request)
		sDB = seqDB.objects.get(**sDB_dict)
		qset = filter__Xhit(sDB.hit4cath2cath_set)
		# qset = CCXhit.filter({'seqDB':sDB.id})
		# crit.update({'seqDB':sDB.id})
		crit.update(read__filter(request))

	# qset = CCXhit.filter(node1__level__letter='H') 
	# qset = CCXhit.filter(**crit)
	# qset = qset.order_by('-ISS_norm')
	# qset = qset.exclude(ISS_norm__gte=0.7).exclude(ISS_raw__lte=10)
	# qset = qset[:1000]
	for k,v in crit.items():
		qset = qset.filter(**{k:v})
	qset = qset.order_by(*order)
	qset = qset[ : limit ]

	return qset

def filter__Xhit(qset):
	return qset 
	# return qset.exclude(Q(node1__parent=F("node2__parent")) & Q(node1__level__letter='S')) 


def read__Cver(request, **kwargs):
	kwargs['default'] = kwargs.get('default', "name 4_1_0")
	d = param2dict(request, 'Cver',**kwargs)
	return d


def init__CCXhit__qset(request = None):
	# letter = 'H'
	# rv_field = reverse_field[letter]
	# crit = {'node1__level__letter':'H'}
	crit = {
	'ISS_norm__gte':0.5,
	'ISS_raw__gte':10,
	}
	limit = 500
	# order = ['-ISS_norm']
	order = []
	if request:
		sDB_dict = read__seqDB(request)
		vdict    = read__Cver(request)
		crit.update(read__filter(request))

		sDB = seqDB.objects.get(**sDB_dict)
		Cver   = version.objects.get(**vdict) 


		qset = filter__Xhit( sDB.hit4cath2cath_set.filter(node1__version = Cver ) )

	for k,v in crit.items():
		qset = qset.filter(**{k:v})
	# qset = CCXhit.filter(**crit)
	qset = qset.order_by(*order)
	qset = qset[ : limit ]

	return qset

def test__CCXhit_homsf(request):
	'''
	##############################
	Experimental and not useful dut to rehitting: same homsf hitting same sequence via different hmm profiles.
	##############################
	'''
	qset = init__CCXhit_homsf(request)

	cols = None

	title = 'ISS_test'
	# orders = []

	figurl = '/tst/figure' + request.get_full_path()
	button1 = blankobj( 
		url = figurl,
		text = '''[scatter]<br/>
		x: ISS_raw<br/>
		y: average hit ''',
		)

	response = view_qset(
		request,
		qset, 
		cols = cols,
		title = title,
		buttons = [button1],
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
		qset = node_stat.objects.in_bulk( homsf_list.values_list('node_stat', flat = True) ).values()
		qset = fake__query_set( qset )

		figurl = '/tst/figure' + request.get_full_path()
		buttons = []
		buttons +=[ blankobj( 
		# url = reverse(scatterplot_domain,args=[x for x in [homsf_id] if x]),
		url = figurl,
		text = '''[scatter]<br/>
		x: superfamily size<br/>
		y: R-squared''',
		)
		]

		return view_qset(request, 
			# homsf_list,
			qset,
				# orders = ['-nDOPE_std'],
				# orders = ['node_stat__Rsq_NBcount_Acount'],

				# cols = ['superfamily_urled','s35_count','s35_len_avg','nDOPE_avg','nDOPE_std'],
				cols = ['superfamily_urled','s35_count',
					'node_stat__Rsq_NBcount_Rcount',
					'node_stat__Rsq_NBcount_Acount',
					'version__name',
					# 's35_len_avg','nDOPE_avg','nDOPE_std',
					],
				buttons = buttons,		
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
		parent = None

	else:
		homsf = classification.objects.get_bytree( homsf_id )[0]
		qset = domain.objects.filter(classification__in=homsf.classification_set.all())
		# domain_list = domain_list.order_by('-nDOPE')

		qset = qset.order_by('-domain_stat__maha_dist')
		try:
			parent = homsf.node_stat
		except:
			parent = None
	return qset,parent

def domain_collection(request, homsf_id = None,
	# crit = {'s35_count__gt':10,},
	):
	'''
	specifying qset		
	'''
	qset,parent = homsf2domain(homsf_id)
	# cols = ['domain_id','superfamily_urled','sf_s35cnt','domain_length','nDOPE'];
	cols = [];

	figurl = '/tst/figure' + request.get_full_path()
	buttons = []
	buttons +=[ blankobj( 
	# url = reverse(scatterplot_domain,args=[x for x in [homsf_id] if x]),
	url = figurl,
	text = '''[scatter]<br/>
	x: atom count<br/>
	y: nbpair count''',
	)
	]
	buttons +=[ blankobj( 
	# url = reverse(scatterplot_domain,args=[x for x in [homsf_id] if x]) + '?scatter=pcnorm',
	url = figurl + '?scatter=pcnorm',
	text = '''[scatter]<br/>
	x: protein size<br/>
	y: packedness''',
	)
	]
	# raise Exception(request.path)
	return view_qset(
		request,
		qset,
		cols=cols,
		title = "s35reps from %s" % (homsf_id) ,
		parent = parent,
		buttons = buttons,
							)
from utils_db import *
# def test__contrast__crosshit(request):

def	init__contrast__crosshit(request):
	Cver = version.objects.get(**read__Cver(request))
	# print Cver
	hmms = HMMprofile.objects.filter(cath_node__version=Cver)
	# raise Exception(hmms)
	# read__param
	sDB1 = seqDB.objects.get(
		**param2dict(request,'seqDB1','name CATH-S40-nr version 4_1_0')
		)
	sDB2 = seqDB.objects.get(
		**param2dict(request,'seqDB2','name crosshit version 4_1_0')
		)
	# sDB1 = seqDB.objects.get(name='CATH-S40-nr',version=)
	# sDB2 = seqDB.objects.get(name='crosshit')
	qset = contrast__crosshit(sDB1,sDB2, hmms)
	return qset
def tab__contrast__crosshit(request,):
	qset = init__contrast__crosshit(request)

	figurl = '/tst/figure' + request.get_full_path()
	button1 = blankobj( 
		url = figurl,
		text = '''[scatter]<br/>
		x: val1<br/>
		y: val2 ''',
		)
	return view_qset(
		request,
		qset,
		buttons = [button1],
		# cols = qset[0].default_cols,
		)

def scatterplot__contrast__crosshit(request):
	qset = init__contrast__crosshit(request)
	fields  = [
		# 'domain__domain_stat__res_count',
		'val1',
		'val2',
		'id',
		# 'superfamily',
		]

	kwargs = 	{
	'title': 'contrast Xhits' ,
	# 'greet': greets["scatterplot__hit4cath2cath"],
	'greet': 'NOTHING yet',
	# 'You are looking at a collection of %s'%qset[0].level.name,	
	'subplot_kwargs':{
		'logx': True,
		'logy': True,
		# 'xlim':[-.2,7.],
		# 'ylim':[-.2,6.],
		'xoffset': 1,
		'yoffset': 1,

		# 'xlabel': field_short[fields[0]],
		# 'ylabel': field_short[fields[1]],

		'regress': True,
		},
	'labels': [str(q) for q in qset],
	}

	return scatterplot_qset(
		request,
		qset,
		fields = fields,
		# title = 'superfamily %s' % homsf_id,
		**kwargs
		)

	# qset = 
############## Use class-based view to replace "scatterplot_qset" in the future #############################
# class scatterplot__view(TemplateView):
# 	template_name = ""
# 	def get_context_data(self):
# 		pass
# 	pass




def scatterplot_qset( request, qset = None, title = None, fields = None, greet = None, crit = [], **kwargs):



	fields_t = request.GET.get('FigFields','+'.join(fields))
	print fields
	# filter = request.GET.get('FigFilter','+'.join(filter)).split('+')
	# print(fields_t)
	# print(kwargs.has_key('subplot_kwargs'))
	# labels = list(qset.values_list('domain__domain_id',flat=True))
	# print kwargs.keys()
	if crit:
		qset = qset.filter(*crit)

	jdict = scatterplot_qset_dict( qset, fields = fields, **kwargs)
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

	qset,parent = homsf2domain(homsf_id)
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
		's35_count',
		'node_stat__Rsq_NBcount_Acount',
		'id',
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






def scatterplot__hit4cath2cath(request, 
	qset = None,
	# crit = {'s35_count__gt':10,}	
	):

	fields  = [
		# 'domain__domain_stat__res_count',
		'hcount_geoavg',
		'ISS_raw',
		'id',
		# 'superfamily',
		]

	kwargs = 	{
	'title': 'hit4cath2cath' ,
	'greet': greets["scatterplot__hit4cath2cath"],
	# 'You are looking at a collection of %s'%qset[0].level.name,	
	'subplot_kwargs':{
		'logx': True,
		'logy': True,
		'xlim':[-.2,7.],
		'ylim':[-.2,6.],
		'xoffset': 1,
		'yoffset': 1,

		'xlabel': field_short[fields[0]],
		# 'ylabel':'Rsq_NBcount_Acount',
		'ylabel': field_short[fields[1]],
		# 'xscale': 'log',
		# 'yscale': 'log',
		'regress': False,
		},
	'labels': [str(q) for q in qset],
	}

	return scatterplot_qset(
		request,
		qset,
		fields = fields,
		# title = 'superfamily %s' % homsf_id,
		**kwargs
		)


def scatterplot__hitlistPR(request, 
	qset = None,
	# crit = {'s35_count__gt':10,}	
	):
	qset,parent = init__hitlistPR(request)
	if isinstance(qset, list):
		qset = fake__query_set(qset)


	fields  = [
		'hit1__bitscore',
		'hit2__bitscore',
		'id',
		# 'superfamily',
		]
	fields = request.GET.get("fields", ' '.join(fields)).split()


	kwargs = 	{
	'title': 'hit4cath2cath' ,
	'greet': greets["scatterplot__hit4cath2cath"],
	# 'You are looking at a collection of %s'%qset[0].level.name,	
	'subplot_kwargs':{
		'logx': False,
		'logy': False,
		# 'xlim':[0,500],
		'xlim':[0,200],
		'ylim':[0,200],
		# 'xlabel': field_short[fields[0]],
		# 'ylabel':'Rsq_NBcount_Acount',
		# 'ylabel': field_short[fields[1]],
		# 'xscale': 'log',
		# 'yscale': 'log',
		'regress': False,
		},
	'labels': [ str(q) for q in qset],
	}
	return scatterplot_qset(
		request,
		qset,
		fields = fields,
		# title = 'superfamily %s' % homsf_id,
		**kwargs
		)


def test__scatterplot__hitlistPR(request, 
	qset = None,
	# crit = {'s35_count__gt':10,}	
	):
	# sDB_dict = {
	# 'name':'CATH',
	# 'version':'v4_1_0',
	# }
	sDB_dict = read__seqDB(request)
	sDB = seqDB.objects.get(**sDB_dict)
	qset = hitlist_compare(sDB = sDB)
	return scatterplot__hitlistPR(request,qset)

def test__scatterplot__hit4cath2cath(request, 
	# crit = {'s35_count__gt':10,}	
	):

	qset = init__CCXhit_homsf(request)

	return scatterplot__hit4cath2cath(request, qset)
def test__scatterplot__CCXhit_homsf(request, 
	# crit = {'s35_count__gt':10,}	
	):
	qset = init__CCXhit_homsf(request)

	return scatterplot__hit4cath2cath(request, qset)

def test__scatterplot__CCXhit(request, 
	# crit = {'s35_count__gt':10,}	
	):
	qset = init__CCXhit__qset(request)

	return scatterplot__hit4cath2cath(request, qset)





def scatterplot_domain_maha(request):
	# dset=domain
	# qset = domain.objects.all()#
	# qset = domain.objects.order_by('-domain_stat__maha_dist')[:1000]#
	qset = classification.objects.exclude(domain__domain_stat__isnull = True)
	qset = qset.order_by('-domain__domain_stat__maha_dist')[:1000]#

	fields = [
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
