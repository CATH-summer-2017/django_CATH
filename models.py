# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
from django.utils import timezone
from django.db import models
from django.db.models import Avg,StdDev,Count
from django.urls import reverse
from django.templatetags.static import static

from django.dispatch import receiver
# from django.contrib.staticfiles.templatetags.staticfiles import static
# 
# import requests
# Create your models here.

from CATH_API.lib import *
import urllib
from .domutil.util import *


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

class blankobj(object):
	def __init__(self,**kwargs):
		for k,v in kwargs.iteritems():
			setattr(self,k,v)
		pass




class homsf_manager(models.Manager):
	def get_queryset(self):
		homsf_qset = super(homsf_manager, self).get_queryset().filter(level_id=5);
		homsf_qset = (homsf_qset.annotate(nDOPE_std=StdDev("classification__domain__nDOPE"))
			  .annotate(nDOPE_avg=Avg("classification__domain__nDOPE"))
			  .annotate(s35_count=Count("classification"))
			  .annotate(s35_len_avg=Avg("classification__domain__domain_length"))
			  # .annotate(superfamily="superfamily")
			  )
		# for homsf_qset 
		return homsf_qset

class node_manager(models.Manager):

	def get_bytree(self, node_str, qnode = None):


		lst = [int(x) for x in node_str.split('.')]
		if lst[-1]:
			lst += [0]
		# if lst[:2] == [0,0]:
		ldep = len(lst)

		lst = [0,0]+lst;

		# idx = (x for x in lst)
		if not qnode:
			level = 2
			obj = super(node_manager, self);
			qset = obj.get_queryset()
			qset = qset.filter(level__id = level)
		else:
			# qset = 
			level = qnode.level.id + 1
			qset = qnode.classification_set
		while 1:
			# qdict = {'level__id':level,
					 # levels[level]: lst[level]}
			try:
				# qnode = qset.get(**qdict)
				qnode = qset.get(**{ levels[level]: lst[level]})
			except:
				resp = 0;
				# print('node %s not found'%(lst[1:level]))
				break

			if level == ldep:
				resp = 1
				break

			qset = qnode.classification_set
			level += 1

		# domain_set = super(node_manager, self).get();
		# domain_set.annotate(superfamily="")
		return (qnode,resp)

	# def get_superfamily(self):
	# 	homsf_qset.manager = "homsf_manager"
class domain_manager(models.Manager):
	def get_queryset(self):
		domain_set = super(domain_manager, self).get_queryset();
		# domain_set.annotate(superfamily="")
		return domain_set
class defer_text_manager(models.Manager):
	def get_queryset(self,*args,**kwargs):
		qset = super(defer_text_manager, self).get_queryset(*args,**kwargs).defer('text');
		# domain_set.annotate(superfamily="")
		return qset

class Question(models.Model):
	question_text = models.CharField(max_length=200)
	pub_date = models.DateTimeField('date published')
	def __str__(self):
		return self.question_text
	def was_published_recently(self):
		return self.pub_date >= timezone.now() - datetime.timedelta(days=1)
	def to_values(self):
		return self

class Choice(models.Model):
	question = models.ForeignKey(Question, on_delete=models.CASCADE)
	choice_text = models.CharField(max_length=200)
	votes = models.IntegerField(default=0)
	def __str__(self):
		return self.choice_text

class version(models.Model):
	name = models.CharField(default=None,max_length=10);
	def __str__(self):
		return self.name;
class level(models.Model):
	name = models.CharField(default=None,max_length=50)
	letter = models.CharField(default=None,max_length=1);
	def __str__(self):
		return self.name;

class classification(models.Model):	
	# homsf_ID = models.CharField(max_length=7, primary_key=True)
	dft = 0

	Class = models.IntegerField(default=dft,null=True,db_index=True)
	arch = models.IntegerField(default=dft,null=True,db_index=True)
	topo = models.IntegerField(default=dft,null=True,db_index=True)
	homsf = models.IntegerField(default=dft,null=True,db_index=True)
	s35 = models.IntegerField(default=dft,null=True,db_index=True)
	s60 = models.IntegerField(default=dft,null=True)
	s95 = models.IntegerField(default=dft,null=True)
	s100 = models.IntegerField(default=dft,null=True)
	version =  models.ForeignKey(version, on_delete= models.CASCADE);
	level = models.ForeignKey(level,  on_delete=models.CASCADE)
	parent = models.ForeignKey("self", default=None,null=True, on_delete=models.CASCADE)
	
	def node_dict(self):
		return {
			'Class':self.Class,
			'arch':self.arch,
			'topo':self.topo,
			'homsf':self.homsf,
			's35':self.s35,
			's60':self.s60,
			's95':self.s95,
			's100':self.s100,
			# 'level_id':self.level_id,
			}
	def find_depth(self, depth):
		s = '';
		i = depth
		if not i:
			return('Not in any Class')
		for key in [self.Class,self.arch,self.topo,self.homsf,self.s35,self.s60,self.s95,self.s100]:
			i += -1
			s += str(key) + '.'
			if not i :
				return s.rstrip('.')
	def __str__(self):
		return self.find_depth(self.level.id)
	
	def superfamily(self):
		return self.find_depth(4)

	def superfamily_urled(self):
		sf = self.superfamily();
		url = reverse('domain_collection',args=[sf])
		htmldom = "<a href=\"{:s}\">{:s}</a>".format(url,sf)
		return htmldom
	
	def get_s35cnt(self):
		url = 'http://www.cathdb.info/version/v4_1_0/api/rest/superfamily/%s' % self.superfamily();
		cnt = fetch_cath(url)[1]["child_count_s35_code"]
		return cnt



	# objects = models.Manager()
	objects = node_manager()
	homsf_objects = homsf_manager()
		# pass

	# 	return("Superfamily %s"%self.homsf_ID())

class node_stat(models.Model):
	node = models.OneToOneField(classification,
		on_delete= models.CASCADE,
		primary_key=True)
	Rsq_NBcount_Acount = models.FloatField(null = True);
	Rsq_NBcount_Rcount = models.FloatField(null = True);




class domain(models.Model):
	domain_id = models.CharField(max_length=7,db_index=True)
	domain_length = models.IntegerField(default=0,null=True)
	resolution = models.FloatField(default=0,null=True)
	nDOPE = models.FloatField(default=0,null=True)
	raw_DOPE = models.FloatField(default=0,null=True)
	# version =  models.ForeignKey(version, default=None,on_delete= models.CASCADE);
	# classification =  models.ForeignKey(classification, on_delete= models.CASCADE);
	classification =  models.OneToOneField(classification, on_delete= models.CASCADE);


	def __str__(self):
		return self.domain_id

	def superfamily(self):
		return(self.classification.superfamily())
	def superfamily_urled(self):
		return(self.classification.superfamily_urled())
	def view_chopped(self):		
		elem = '<a id="view3d" href="#view_{:s}" data-toggle="collapse"><img src="{:s}" alt="chopped_pdb"/></a>'.format( self.domain_id, static("imgs/rasmol.png"))
		return elem
	def domain_id_urled(self):
		version = 'current';
		url = "http://www.cathdb.info/version/{:s}/domain/{:s}/".format(version, self.domain_id)
		elem = '<a target="_blank" href="{:s}">{:s}</a>'.format(url, self.domain_id)
		return elem
	def residue_count(self):
		try: 
			c = self.domain_stat.res_count
		except Exception as e:
			c = None
			# print(e)
		return (c)
	def nbpair_count(self):
		try: 
			c = self.domain_stat.nbpair_count
		except Exception as e:
			c = None
			# print(e)
		return (c)
	def atom_count(self):
		try: 
			c = self.domain_stat.atom_count
		except Exception as e:
			c = None
			# print(e)
		return (c)
	
	# class_id = models.IntegerField(default=0)
	# node = models.CharField(default=None)
	# homsf = models.ManyToManyField(homsf);

class domain_stat(models.Model):
	domain = models.OneToOneField(domain,
		on_delete = models.CASCADE,
		primary_key=True);
	DOPE = models.FloatField(null = True)
	nDOPE = models.FloatField(null = True)
	nbpair_count = models.IntegerField(null = True)
	atom_count = models.IntegerField(null = True)
	res_count = models.IntegerField(null = True)
	maha_dist = models.FloatField(null = True)
	pcx = models.FloatField(null = True)
	pcy = models.FloatField(null = True)



class s35_rep(domain):
	# classification = models.ForeignKey(classification, default=None,on_delete= models.CASCADE);
	pass
	# rep_type = models.CharField(default='s35',max_length=4);
	# domain.rep_type='s35';
	# self.save()

### The following model is for ISS proj.
### This 
class seqDB(models.Model):
	name = models.CharField(default=None,max_length=20);
	version =  models.CharField(default=None,max_length=10);
	def __str__(self):
		return self.name + "_Ver:" + self.version



class sequence(models.Model):
	seqDB = models.ForeignKey(seqDB, on_delete= models.CASCADE);
	acc = models.CharField(  max_length=12, db_index = True)
	subversion = models.IntegerField(default = 0)
	length = models.IntegerField()
	cath_node = models.ForeignKey(classification, null = True, on_delete= models.CASCADE);
	def __str__(self):
		return  "%s from %s" % (self.acc, str(seqDB) )
	def full_acc(self):
		return "%s.%d" % ( self.acc, self.subversion)
	def GETcath_node(self):
		try:
			d = domain.objects.get(self.acc)
			node = d.classification
		except:
			node = None
		return node


class HSPfrag(models.Model):
	### The HSPfrag may be discontinuous in itself. HMMsearch only outputs the start and end, which is noted here.
	sequence = models.ForeignKey(sequence, on_delete= models.CASCADE);
	start = models.IntegerField(default = None)
	end = models.IntegerField(default= None)
	raw = models.BooleanField(default = 1)
	def is_valid(self):
		valid = self.start > 0 and self.end > self.start and self.sequence.length > self.end  
		return valid
	def span_str(self):
		return "%d-%d" % (self.start, self.end)
	def __str__(self):
		return "HSP fragment on %s, span [%s]" % (self.sequence.name,self.span_str())



class HMMprofile(models.Model):
	# cath_node = models.ForeignKey(classification, default = None, on_delete= models.CASCADE);
	# rep_domain = models.ForeignKey(domain, on_delete = models.CASCADE)
	# sequence = models.ForeignKey( sequence, on_delete = models.CASCADE);
	# cath_node = sequence.cath_node 
	# locator = models.CharField( max_length=50 )
	# start = models.IntegerField(null = True)
	# end = models.IntegerField( null = True)

	cath_node = models.OneToOneField(classification, on_delete = models.CASCADE);
	# cath_node = models.OneToOneField(classification, on_delete = models.CASCADE);
	# hitseq = models.ManyToManyField( HSPfrag )
	hits = models.ManyToManyField( sequence, through = 'hit4hmm2hsp' )
	length = models.IntegerField(default = None)


	text = models.TextField(blank = True, null = True)
	objects = defer_text_manager()
	# def fill_span(self):
	# 	lst = locator.split('_')
	# 	self.start = lst[ 0].split("-")[ 0]
	# 	self.end   = lst[-1].split("-")[-1]
	# 	self.save()
	# 	return [self.start,self.end]
	# def span_str(self):
	# 	if not self.start or not self.end:
	# 		self.fill_span()
	# 	return "%d-%d" % (self.start, self.end)
	def __str__(self):
		return "HMM for %s " % self.cath_node


class hit4hmm2hsp(models.Model):
	query = models.ForeignKey( HMMprofile, on_delete = models.CASCADE)
	
	target = models.ForeignKey( sequence, on_delete = models.CASCADE)
	start = models.IntegerField(default = None)
	end = models.IntegerField(default= None)
	

	logCevalue=models.FloatField(default = None)
	logIevalue=models.FloatField(default = None)
	bitscore = models.FloatField(default = None)
	bias = models.FloatField(default = None)
	acc_avg = models.FloatField(null = True)

	
	def __str__(self):
		return "Query:%s \nTarget:%s" % ( str(self.query), str(self.target) )

	

bfmt = '<b>%s</b>' 
class hit4cath2cath(models.Model):
	node1 = models.ForeignKey( classification, on_delete = models.CASCADE, related_name = 'node1')
	node2 = models.ForeignKey( classification, on_delete = models.CASCADE, related_name = 'node2')
	ISS_raw = models.IntegerField( default = None  )
	ISS_norm = models.FloatField( default = None )
	seqDB = models.ForeignKey(seqDB, on_delete= models.CASCADE);
	def __str__(self):
		# return "Node 1: %s,  Node 2: %s,  "
		# basefmt = 
		raw_msg = "[CATH_CATH_ISShit<]:[Node1: %s ,Node2: %s]< raw_ISS: %d, norm_ISS: %.2f >(from  %s )" % (
			self.node1,
			self.node2, 
			self.ISS_raw, 
			self.ISS_norm,
			self.seqDB)
		html_msg = "[<b>CATH_CATH_ISShit</b>]:[Node1: %s ,Node2: %s]< raw_ISS: %s, norm_ISS: %s  >(from %s )" % (
			bfmt % self.node1,
			bfmt % self.node2, 
			bfmt % ( '%d' % self.ISS_raw ) , 
			bfmt % ( '%.2f'%self.ISS_norm) ,
			bfmt % self.seqDB)
		return (html_msg)

	def __str__(self):
		# return "Node 1: %s,  Node 2: %s,  "
		# basefmt = 
		raw_msg = "[CATH_CATH_ISShit]:[Node1: %s ,Node2: %s]< raw_ISS: %d, norm_ISS: %.2f >(from  %s )" % (
			self.node1,
			self.node2, 
			self.ISS_raw, 
			self.ISS_norm,
			self.seqDB)
		return (raw_msg)
	def __str__(self):
		# return "Node 1: %s,  Node 2: %s,  "
		# basefmt = 
		raw_msg = "[Node1: %s ,Node2: %s]" % (
			self.node1,
			self.node2, 
			)
		return (raw_msg)
	def xhit_urled(self, db_source = "Crosshits_v4_1_0",**kwargs):
		"http://xhits.cathdb.info/crosshits.php?sf2=2.130.10.80&sf1=2.120.10.80&db_source=Crosshits_v4_1_0"
		baseurl = "http://xhits.cathdb.info/crosshits.php"
		# url = "http://www.cathdb.info/version/{:s}/domain/{:s}/".format(version, self.domain_id)
		# url = self.node1.superfamily()
		pdict = kwargs
		pdict.update(
			{'sf1': self.node1.superfamily(),
			 'sf2': self.node2.superfamily(),
			 'db_source': db_source,
			 }
		)
		# if "db_source" not in kwargs.keys():
		pstr = urllib.urlencode(pdict)
		url = "%s?%s" % (baseurl,pstr)

		return a_href( db_source , url )
	def local_CCXhit(self):
		param = urllib.urlencode( {
			"node1__id":self.node1.id,
			"node2__id":self.node2.id,
			} )
		url = reverse('CCXhit_handler',args=[])
		return a_href("local_page", "%s?%s" % (url , param) )
	def compare_hitlist(self):
		pstr = urllib.urlencode( {
			"node1__id":self.node1.id,
			"node2__id":self.node2.id,
			} )
		# url = reverse('CCXhit_handler',args=[])
		baseurl = reverse("tab__hitlist__pair",args=[])
		url = "%s?%s" % (baseurl,pstr)

		return a_href("compare_hitlist", url)		

	def OLD1_compare_hitlist(self):

		#node1 = classification.objects.filter(id = self.node1.id)
		rv_field = reverse_field[self.node1.level.letter]
		rv_field = rv_field.replace('__hits','__hit4hmm2hsp__id')
		hitlist1 = classification.objects.filter(id = self.node1.id).values_list(rv_field,flat = True) 

		rv_field = reverse_field[self.node2.level.letter]
		rv_field = rv_field.replace('__hits','__hit4hmm2hsp__id')
		hitlist2 = classification.objects.filter(id = self.node2.id).values_list(rv_field,flat = True) 
		baseurl = reverse("tab__hitlist__pair",args=[])
		pstr = urllib.urlencode( {
			"hitlist1":hitlist1,
			"hitlist2":hitlist2,
			} )
		url = "%s?%s" % (baseurl,pstr)
		return a_href("compare_hitlist", url)
		# self





	def OLD_compare_hitlist(self):
		hmmid1 = self.node1.hmmprofile.id if self.node1.level.letter == 'S' else None
		hmmid2 = self.node2.hmmprofile.id if self.node2.level.letter == 'S' else None
		baseurl = reverse("hmm_compare",args=[])
		pstr = urllib.urlencode( {
			"hmm1__id":hmmid1,
			"hmm2__id":hmmid2,
			} )

		url = "%s?%s" % (baseurl,pstr)

		# rv_field()

		return a_href("compare_hitlist", url)

	hcount_geoavg = models.FloatField( default = None, null = True)
	def update_hcount_geoavg(self):
		qset1 = self.node1.hit_summary_set.filter(seqDB = self.seqDB)
		qset2 = self.node2.hit_summary_set.filter(seqDB = self.seqDB)
		if qset1.exists() and qset2.exists():
			h1 = qset1.first().hcount
			h2 = qset2.first().hcount
			gavg = (h1*h2)**0.5
		else:
			gavg = None
		self.hcount_geoavg = gavg
		return gavg

		# self.node1.id
# @receiver(models.signals.post_save, sender=hit4cath2cath)
# def execute_after_save(sender, instance, created, *args, **kwargs):
#     if created:
#     	instance.update_hcount_geoavg()
#     	instance.save()



# @receiver(models.signals.post_init, sender=hit4cath2cath)
# def execute_after_init(sender, instance, *args, **kwargs):
# 	instance.update_hcount_geoavg()



    	# instance.save()
# code
# def ISSstat():

class hit_summary(models.Model):
	node = models.ForeignKey(classification, on_delete=models.CASCADE);
	seqDB = models.ForeignKey(seqDB, on_delete=models.CASCADE);
	hcount = models.IntegerField(default = 0) #### Auto-update in the future




class hitP_obj(blankobj):
	def __init__(self,**kwargs):
		return blankobj.__init__(self, **kwargs)
		# return super(hitP_obj, self).__init__(**kwargs)
	def __str__(self):
		return '%s: %2.1f  %2.1f' % (self.acc, self.hit1.bitscore, self.hit2.bitscore)


def hitlist_compare(node1__id = 309754, node2__id = 310524, sDB = None, **kwargs):
    sDB_id = sDB.id

    qset1 = classification.objects.filter(id = node1__id)
    qset2 = classification.objects.filter(id = node2__id)

    node1 = qset1[0]
    node2 = qset2[0]


    rv_field = reverse_field[ node1.level.letter ]
    sDB_field  = rv_field + "__seqDB"
    text_field = rv_field.replace('__hits','__text')
    rvid_field = rv_field.replace('__hits','__hit4hmm2hsp__id')

    fs = [rv_field, rvid_field, sDB_field]
    hitlist1 = qset1.values_list(*fs).distinct() 

    
    rv_field = reverse_field[ node2.level.letter ]
    sDB_field  = rv_field + "__seqDB"
    text_field = rv_field.replace('__hits','__text')
    rvid_field = rv_field.replace('__hits','__hit4hmm2hsp__id')
    
    fs = [rv_field, rvid_field, sDB_field]
    hitlist2 = qset2.values_list(*fs).distinct() 



    
    hits1_ids = {seqid:hitid for seqid,hitid,sid in hitlist1 if sid == sDB_id}
    hits2_ids = {seqid:hitid for seqid,hitid,sid in hitlist2 if sid == sDB_id}
    inter_ids = set(hits1_ids) & set(hits2_ids)

    hits1_obj = hit4hmm2hsp.objects.in_bulk( [hits1_ids[i] for i in inter_ids] )
    hits2_obj = hit4hmm2hsp.objects.in_bulk( [hits2_ids[i] for i in inter_ids] )

    # print len(inter_ids)
    qset = [ 
    hitP_obj(
        id = i,
        acc = hit1.target.acc,
        hit1 = hit1,
        hit2 = hit2) for i,hit1,hit2 in 
        izip(
            inter_ids,hits1_obj.values(),hits2_obj.values()
        )

    ]


    return qset



# class Publisher(models.Model):
#     name = models.CharField(max_length=30)
#     address = models.CharField(max_length=50)
#     city = models.CharField(max_length=60)
#     state_province = models.CharField(max_length=30)
#     country = models.CharField(max_length=50)
#     website = models.URLField()

#     class Meta:
#         ordering = ["-name"]

#     def __str__(self):              # __unicode__ on Python 2
#         return self.name

# class Author(models.Model):
#     salutation = models.CharField(max_length=10)
#     name = models.CharField(max_length=200)
#     email = models.EmailField()
#     headshot = models.ImageField(upload_to='author_headshots')

#     def __str__(self):              # __unicode__ on Python 2
#         return self.name

# class Book(models.Model):
#     title = models.CharField(max_length=100)
#     authors = models.ManyToManyField('Author')
#     publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
#     publication_date = models.DateField()