from django.conf.urls import url
from . import views, review_views, views_extra
from django.contrib.auth.decorators import login_required

urlpatterns = [ 

	url(r'^sh-rej-list/$', review_views.view_short_rej_list,
		name="sh-rej-list"),  

	url(r'^prog-change-list/$', review_views.prog_change_list,
		name='prog-change-list'),

	url(r'^final-osc-list/$', review_views.submit_osc_list,
		name='final-osc-list'),
	
	url(r'^final-pc-list/$', review_views.submit_pc_list,
		name='final-pc-list'),

	url(r'^accept-offer-later/$', review_views.acceptOffer_later,
		 name='accept-offer-later'),

	url(r'^esc-applicant/$', review_views.esc_applicants,
		 name='esc-applicant'),
	
	url(r'^ajax-data/(?P<pg>\d+)/(?P<st>[\w\-\s\.\,]+)/(?P<pg_typ>[\w\-\s]+)/(?P<adm_bat>[\w\-\s]+)$',
	 review_views.MyDataView.as_view(), name='table_data'),
	
	url(r'^bulk-ajax-data/(?P<pg>\d+)/(?P<lo>\d+)/$',
	 review_views.BulkMailFilterPagingView.as_view(),
	  name='bulk_table_data'),
	
	url(r'^program-ajax-validate/$',
	 review_views.pgram_change_ajax_validate,
	  name='pg_ch_ajax'),
	
	url(r'^offer-ajax-list/$',
	 review_views.offer_change_list_ajax,
	  name='offer_ajax_list'),

	url(r'^prog-ajax-list/$',
	 review_views.prog_change_list_ajax,
	  name='prog_ajax_list'),

	url(r'^rev-man-id-gen/(?P<app_id>\d+)/$',
	 review_views.rev_manID_gen,
	  name='man_id_gen'),

	url(r'^name-change-list/$', review_views.name_change_list,
	  name='name-change-list'),

	url(r'^sdms-progress$', review_views.sdms_progress, name='sdms_progress'),

	url(r'^name-change-form/(?P<application_id>\d+)/$', review_views.name_change_form,
	  name='name-change-form'),

	url(r'^ncl_ajax_data/(?P<pg>\d+)/(?P<ab>[\d\-\s]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
	 review_views.NclDataView.as_view(), name='ncl-table-data'),

	url(r'^dmr_report_specific/$',
	 views_extra.DMR.as_view(),{'program_type': ['specific',],
	 'title':'DMR - Program wise - Specific Programs'}, name='dmr-spec'),

	url(r'^dmr_report_cluster/$',
	 views_extra.DMR.as_view(),{'program_type': ['cluster',],
	 'title':'DMR - Program wise - Cluster Programs'}, name='dmr-cluster'),

	url(r'^dmr_report_non_specific/$',
	 views_extra.DMR.as_view(), {'program_type': ['non-specific',],
	 'title':'DMR - Program wise - Non-Specific Programs'}, name='dmr-non-spec'),

	url(r'^dmr_daily__non_specific/$',
	 views_extra.DMRNonSpecific.as_view(), name='dmr-daily-non-spec'),
	url(r'^fee-waiver-report/$', views_extra.WaiverReport.as_view(),
	  name='waiver-report'),
	url(r'^fee-waiver-report-ajax/(?P<b_id>[\d\-\s]+)/$',
	 views_extra.WaiverReportDataView.as_view(),
	  name='waiver-report-ajax'),
	
	url(r'^milestone-report/$', views_extra.ApplicationMilestoneReport.as_view(),
	  name='milestone-report'),
	url(r'^milestone-report-ajax/(?P<b_id>[\d\-\s]+)/(?P<p_id>[\d]+)/(?P<p_type>[\w\-\s\.\,]+)/$', views_extra.MilestoneView.as_view(),
	  name='milestone-report-ajax'),

	url(r'^bulk-regenerate/$', views_extra.bulk_regenerate,
	  name='bulk-regenerate'),

	url(r'^rev-regen-offer/(?P<ap_id>\d+)/$',views_extra.rev_regen_offer, 
		name='rev_regen_offer'),

	url(r'^review-applicantion-details/(?P<alert_status>\d)/(?P<application_id>\d+)/$',
		review_views.ReviewApplicationDetails.as_view(),
		name='review_application_details'),

	url(r'^prog-change-report/$', views_extra.ProgramChangeReport.as_view(),
	  name='prog-change-report'),
	url(r'^prog-change-report-ajax/(?P<b_id>[\d\-\s]+)/$', 
	  views_extra.ProgChangeReportAjax.as_view(),
	  name='prog-change-report-ajax'),

	url(r'^prog-loc-report-cluster/$',
		views_extra.ProgramLocationReport.as_view(),
		{'program_type':['cluster',],'content_title':'Cluster'}, name='prog-loc-report-cluster'),
	url(r'^prog-loc-report-specific/$',
		views_extra.ProgramLocationReport.as_view(),
		{'program_type':['specific',],'content_title':'Specific'}, name='prog-loc-report-specific'),

	url(r'^application-exception/$', views_extra.ApplicationExceptionView.as_view(),
    	name='app-exp'),
  	url(r'^application-exception-ajax/$',
    	views_extra.AEView.as_view(),name='app-exp-ajax'),

  	url(r"^direct-url-for-application/(?P<pg_code>\w+)/(?P<source_site>\w+)/$",
  		views.direct_url_for_application,
  		name="direct-url-for-application"),

  	url(r'^submit-deferred-docs/$',
		views_extra.DeffDocsUpload.as_view(), name='submit-deferred-mandatory-docs'),

  	url(r'^deferred-docs-app/$',
		views_extra.DefDocsAppData.as_view(),name='deferred-docs-app'),
	url(r'^deferred-docs-app-ajax/(?P<pg>\d+)/(?P<st>[\w\-\s\.\,]+)/(?P<adm_bat>[\w\-\s]+)$',
		views_extra.DefDocsAppAjaxData.as_view(), name='def-doc-ajax'),

	url(r'^view-elective-selections/$',
		views_extra.ElectiveSelectionsAppData.as_view(),name='view-elective-selections'),
	url(r'^view-elective-selections-ajax/(?P<pg>\d+)$',
		views_extra.ElectiveSelectionsAppAjaxData.as_view(), name='view-elective-selections-ajax'),

	url(r'^deferred-docs-sub/$',
		views_extra.DefDocsSubData.as_view(),name='deferred-docs-sub'),
	url(r'^deferred-docs-sub-ajax/(?P<pg>\d+)/(?P<st>[\w\-\s\.\,]+)/(?P<adm_bat>[\w\-\s]+)$',
		views_extra.DefDocsSubAjaxData.as_view(), name='def-doc-sub-ajax'),
	url(r'^emi-report/$',
		views_extra.EMIReportAppData.as_view(),name='emi-report'),
	url(r'^emi-report-ajax/(?P<pg>\d+)/(?P<b_id>[\d\-\s]+)/(?P<st>[\w\-\s\.\,]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
		views_extra.EMIReportAppAjaxData.as_view(), name='emi-report-ajax'),

	url(r'^deferred_application_details/(?P<application_id>\d+)/$',
		views_extra.DeferredApplicationDetails.as_view(),
		name='deferred_application_details'),

	url(r'^deferred_application_details_alert/(?P<alert_status>\d)/(?P<application_id>\d+)/$',
		views_extra.DeferredApplicationDetails.as_view(),
		name='deferred_application_details_alert'),

	url(r'^pre-sel-rej-app/$',
        views_extra.PreSelAppData.as_view(),name='pre-sel-rej-app'),
    
    url(r'^pre-sel-rej-app-ajax/(?P<pg>\d+)/(?P<loc>\d+)$',
        views_extra.PreSelAppAjaxData.as_view(), name='pre-sel-rej-app-ajax'),

    url(r'^dmr_daily__certification/$',
		views_extra.Rev_DMRCertification.as_view(), name='dmr-daily-certification'),

    url(r'^dmr-daily-cluster/$',
		views_extra.Rev_DMRCluster.as_view(), name='dmr-daily-cluster'),
	
	url(r'^dmr-daily-specific/$',
		views_extra.Rev_DMRSpecific.as_view(), name='dmr-daily-specific'),

	url(r'^program-admissions-report/$',
		views_extra.ProgramAdmissionsReport.as_view(), name='program-admissions-report'),
	
	url(r'^program-admissions-report-ajax/(?P<pg>\d+)/(?P<pg_type>[\w\-\s\.\,]+)/(?P<adm_btc>[\w\-\s]+)$',
		views_extra.ProgramAdmissionsReportAjax.as_view(), name='program-admissions-report-ajax'
	 ),

	url(r'^emi-report-eduv/$',
		views_extra.EMIReportEduvAppData.as_view(),name='emi-report-eduv'),
	url(r'^emi-report-eduv-ajax/(?P<pg>\d+)/(?P<b_id>[\d\-\s]+)/(?P<st>[\w\-\s\.\,]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
		views_extra.EMIReportEduvAppAjaxData.as_view(), name='emi-report-eduv-ajax'),

	url(r'^adminapplicationarchiveViews/(?P<pk>\d+)/(?P<run_id>\d+)/$',
        views_extra.ApplicationAdminArchiveView.as_view(),
        name="admin-application-archive-views"),

	url(r'^emi-report-ezcred/$',
		views_extra.EMIReportEzcredAppData.as_view(),name='emi-report-ezcred'),
	url(r'^emi-report-ezcred-ajax/(?P<pg>\d+)/(?P<b_id>[\d\-\s]+)/(?P<st>[\w\-\s\.\,]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
		views_extra.EMIReportEzcredAppAjaxData.as_view(), name='emi-report-ezcred-ajax'),	
	]
