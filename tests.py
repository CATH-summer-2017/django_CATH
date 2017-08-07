# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from .models import *
from datetime import datetime
from django.db import connection
from django.urls import reverse
from django.test import Client


# c = Client(
#     REMOTE_ADDR='127.0.0.1:8001',
#            HTTP_USER_AGENT='Mozilla/5.0', 
#            HTTP_HOST='localhost',)

def check_size(c, url, lim):

	r = c.get(url)
	l  = len(r._container[0])
	if lim > 0:
		assert l >= lim , 'Webpage %s is too small, Expected: >%d, Actual: %d' %(url, lim, l)
	else:
		lim = - lim
		assert l < lim , 'Webpage %s is too big, Expected: >%d, Actual: %d' %(url, lim, l)

	print("checked %s, status code:%d" % (url, r.status_code))
	return(l)


def lookup(node,db_version):
	lst = (int(x) for x in node.split('.'))
	c = classification.objects.get(
		Class=next(lst,0),
		arch=next(lst,0),
		topo=next(lst,0),
		homsf=next(lst,0),
		s35=next(lst,0),
		s60=next(lst,0),
		s95=next(lst,0),
		s100=next(lst,0),
		version__name=db_version
		)
	return c 

# Create your tests here.
class EntryModelTest(TestCase):

	# fixtures = ['c410_s35_fixed.json']y 
	# fixtures = [
	# 'test2000'
	# ]
	fixtures = [
	'test_temp.json'
	]
	def test_homepage(self):
		response = self.client.get('/tst/test/')
		# self.assertEqual(response.status_code, 200)
		assert response.status_code < 400, 'Index page not working, HTTP %d'%response.status_code

	def test_domain_homepage(self):
		response = self.client.get('/tst/domain/')
		request = response.wsgi_request
		print(request)
		assert response.status_code < 400, 'Default domain collection PAGE not reachable, HTTP %d'%response.status_code

	def test_superfamily_homepage(self):
		response = self.client.get('/tst/superfamily/')
		request = response.wsgi_request
		print(request)
		assert response.status_code < 400, 'Default superfamily collection PAGE not reachable, HTTP %d'%response.status_code

	def test_domain(self):
		c = self.client

		expdom = '2.30.39.10'
		url = reverse('domain_collection',args=[expdom])
		response = self.client.get(url)
		l1 = check_size(c,url,20000)

		expdom = '4.3.2.1'
		url = reverse('domain_collection',args=[expdom])
		response = self.client.get(url)
		l2 = check_size(c,url,0001)
		assert l2<l1-1000,'empty page is not smaller than filled page'
		# assert response.status_code >= 401,'%s returned %d'%(url,response.status_code)

	def test_scatterdoamin_raw(self):

		expdom = '2.30.39.10'
		c = self.client
		url = reverse('scatterplot_domain', kwargs={'homsf_id':expdom}) 
		check_size(c,url,30000)

	def test_scatterdomain_pcnorm(self):
		expdom = '2.30.39.10'
		c = self.client
		url = reverse('scatterplot_domain', kwargs={'homsf_id':expdom}) + '?scatter=pcnorm'
		check_size(c,url,30000)

	def test_scatterhomsf_raw(self):	
		c = self.client
		url = reverse('scatterplot_homsf',    )
		check_size(c,url,60000)

		# url = reverse('scatterplot_homsf',) 
		# check_size(c,url,60000)
		pass 
	def test_dups_node(self):
		### ATM the "id" does not contain the hierarchial information thus not so useful
		dupes = ( classification.objects.values('id')
		    .annotate(ct = Count('id')) 
		     .filter(ct__gt=1)
		)
		assert len(dupes)==0		
	# def sest_superfamily(self):
	# 	# 1.10.3460.10	
	# 	node = '1.10.3460.10'
	# 	lst = (int(x) for x in node.split('.'))
	# 	c = classification.objects.get(
	# 		Class=next(lst,None),
	# 		arch=next(lst,None),
	# 		topo=next(lst,None),
	# 		homsf=next(lst,None),
	# 		s35=next(lst,None),
	# 		s60=next(lst,None),
	# 		s95=next(lst,None),
	# 		s100=next(lst,None)
	# 		)
	# 	l = len( c.domain_set.all() )
	# 	assert l > 1, 'Node %s does not associate to multiple (>1) domains '

	# def st_classification(self):
	# 	# self.fail("TODO Test incomplete")
	# 	# for i in range(2):
	# 	c = classification(
	# 		Class=1,
	# 		arch=10,
	# 		topo=10,
	# 		homsf=10,
	# 		s35=283)
	# 	c.save()
	# 	# c.refresh_from_db()

	# 	q = classification.objects.raw('select * from tst_classification;')
	# 	print(q[0])
	# 	qus = Question(question_text='tstqus',pub_date=datetime.now())
	# 	qus.save()
	# 	# q = Question.objects.raw('select * from tst_question')
	# 	# print(q.values())

	# 	from django.db import connection

	# 	with connection.cursor() as c:
	# 			c.execute("show columns from tst_classification")
	# 			print(c.fetchone())

	# 			c.execute("select * from tst_classification")
	# 			row = c.fetchone()
	# 			print(row)

	# def test_relationship(self):
	# 	# 1.10.3460.10	
	# 	node = '1.10.10.10'
	# 	correct_cnt = 407
	# 	db_version = 'v4_1_0'

	# 	sf = lookup('1.10.10.10','v4_1_0')

	# 	real_cnt = len( sf.classification_set.all() )
	# 	assert real_cnt == correct_cnt, 'Node %s does not the correct number of children nodes (Tested %d, should be %d)' % (	
	# 		  node, real_cnt, correct_cnt) 

		
	# 	# print(classification.objects.all())

	# 	# c = classification(
	# 	# 	Class=2,
	# 	# 	arch=10,
	# 	# 	topo=10,
	# 	# 	homsf=10,
	# 	# 	s35=283)
	# 	# c.save()
	# 	pass

	# def test_homepage(self):
	# 	# response = self.client.get('/')
	# 	# print('HTTP %d')
	# 	assert response.status_code < 400, 'Index page not working, HTTP %d'%response.status_code


	# Class = models.IntegerField(default=None)
	# arch = models.IntegerField(default=None)
	# topo = models.IntegerField(default=None)
	# homsf = models.IntegerField(default=None)
	# s35 = models.IntegerField(default=None)
	# s60 = models.IntegerField(default=None)
	# s95 = models.IntegerField(default=None)
	# s100 = models.IntegerField(default=None)
	# level = models.ForeignKey(level, default=None, on_delete=models.CASCADE)
	# version =  models.ForeignKey(version, default=None,on_delete= models.CASCADE);