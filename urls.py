from django.conf.urls import url,include

from . import views

urlpatterns = [

    # url(r'^publishers/$', views.PublisherList.as_view()),

    # ex: /tst/
    # url(r'^$', views.index, name='index'),

	# ex: /tst/hello    
    url(r'^$', views.index, name='hello'),

    url(r'^test/$', views.test, name='test'),
    url(r'^test/CCXhit$', views.test__CCXhit, name='test'),
    url(r'^test/CCXhit_homsf$', views.test__CCXhit_homsf, name='test'),
    url(r'^test/hmm_compare$', views.test__hmm_compare, name='test'),


    url(r'^hmm_compare$', views.test__hmm_compare, name='hmm_compare'),

    url(r'^hitlist_compare/$', views.tab__hitlist__pair, name='tab__hitlist__pair'),
    url(r'^figure/tst/hitlist_compare/$', views.scatterplot__hitlistPR,),
    # url(r'^figure/tst/hitlist_compare$', views.test__scatterplot__hitlistPR, name='test'),

    # url(r'^figure/tst/test/CCXhit_homsf$', views.test__scatterplot_hit4cath2cath, name= 'test'),

    url(r'^CCXhit/$', views.test__CCXhit, name='CCXhit_handler'),





    # ex:/tst/domain
    url(r'^domain/$',
    	views.domain_collection,
    	name = 'domain_collection'),

    # ex:/tst/domain/d1fpzD00/
    url(r'^domain/(?P<domain_id>[\d,a-z,A-Z]+)/$',
    	views.domain_detail,
    	name = 'domain_detail'),

	# ex:/tst/superfamily/3.90.190.10/    
    url(r'^superfamily/$',
        views.homsf_collection,
        name = 'homsf_collection'),

	url(r'^superfamily/id/(?P<homsf_id>[\d,\.]+)/$',
        views.domain_collection,
        name = 'domain_collection'),

	# url(r'^superfamily/(?P<homsf_id>[\d,\.]+)/$',
	# 	views.homsf_s35_collection,
	# 	name = 'homsf_s35_collection'),


    ## Test figures suite
    url(r'^view3d$', views.view3d, name='hello'),
    url(r'^figure/scplot$', views.scatterplot_homsf, {'homsf_id':'1.10.30.10'},name= 'test'),
    url(r'^figure/scplot_err$', views.scatterplot_homsf, {'homsf_id':'1.10.60.10'},name= 'test'),



    url(r'^figure/hit4cath2cath$', views.test__scatterplot_hit4cath2cath, name= 'test'),
    url(r'^figure/tst/test/CCXhit_homsf$', views.test__scatterplot_hit4cath2cath, name= 'test'),

    # url(r'^figure/handler/$',views.scatterplot_qset,name='figure_handler'),
    # url(r'^figure/superfamily/(?P<homsf_id>[\d,\.]+)/$', views.scatterplot_homsf,name='fig_nbscatter'),


    # url(r'^superfamily/id/(?P<homsf_id>[\d,\.]+)/figure$', views.scatterplot_homsf,name='fig_nbscatter'),
    # url(r'^superfamily/figure$', views.scatterplot_homsfM,name='fig_nbscatter'),
    url(r'^figure/tst/superfamily/id/(?P<homsf_id>[\d,\.]+)/$', views.scatterplot_domain,name='scatterplot_domain'),
    url(r'^figure/tst/superfamily/$', views.scatterplot_homsf,name='scatterplot_homsf'),
    url(r'^figure/tst/domain/$', views.scatterplot_domain,name='scatterplot_domain_default'),

   
    url(r'^figure(?P<url>.*)$',views.redirect,name='figure_reverse'),### WTF do I need this handler???????

]
