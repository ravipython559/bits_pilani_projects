from django.conf.urls import url, include
from . import views


urlpatterns = [

	url(r'^sub-reviewer-review-applicant-data/$', 
		views.RAData.as_view(),
		name="review_applicant_data"),
	url(r'^sub-reviewer-ajax-data/(?P<pg>\d+)/(?P<st>[\w\-\s\.\,]+)/(?P<pg_typ>[\w\-\s]+)/$',
		views.MyDataView.as_view(), name='table_data'),
	url(r'^createRCSV/$', views.RCSV.as_view(),
		name="createRCSV"),

	url(r'^dmr_report_specific/$',
		views.DMR.as_view(),{'program_type': ['specific',],
		'title':'DMR - Program wise - Specific Programs'}, name='dmr-spec'), 
	url(r'^dmr_report_cluster/$',
		views.DMR.as_view(),{'program_type': ['cluster',],
		'title':'DMR - Program wise - Cluster Programs'}, name='dmr-cluster'),
	url(r'^dmr_report_non_specific/$',
		views.DMR.as_view(), {'program_type': ['non-specific',],
		'title':'DMR - Program wise - Non-Specific programs'}, name='dmr-non-spec'),
	url(r'^dmr_daily__non_specific/$',
		views.DMRNonSpecific.as_view(), name='dmr-daily-non-spec'),

	url(r'^fee-waiver-report/$', views.WaiverReport.as_view(),
		name='waiver-report'),
	url(r'^fee-waiver-report-ajax/(?P<b_id>[\d\-\s]+)/$',
            views.WaiverReportDataView.as_view(),
      name='waiver-report-ajax'),

	url(r'^milestone-report/$', views.ApplicationMilestoneReport.as_view(),
		name='milestone-report'),
	url(r'^milestone-report-ajax/(?P<b_id>[\d\-\s]+)/(?P<p_id>[\d]+)/(?P<p_type>[\w\-\s\.\,]+)/$', views.MilestoneView.as_view(),
		name='milestone-report-ajax'),
	url(r'sub-review-application-details/(?P<application_id>\d+)/$',
		views.ApplicantDetail.as_view(),
		name='sub-review-application-details'),
	url(r'sub-review-application-details-view/(?P<application_id>\d+)/$',
		views.ApplicantDetailView.as_view(),
		name='sub-review-application-details-view'),

	url(r'^prog-change-report/$', views.ProgramChangeReport.as_view(),
		name='prog-change-report'),
	url(r'^prog-change-report-ajax/(?P<b_id>[\d\-\s]+)/$', 
		views.ProgChangeReportAjax.as_view(),
		name='prog-change-report-ajax'),

    url(r'^prog-loc-report-cluster/$',
		views.ProgramLocationReport.as_view(),
		{'program_type':['cluster',],'content_title':'Cluster'}, name='prog-loc-report-cluster'),
	url(r'^prog-loc-report-specific/$',
		views.ProgramLocationReport.as_view(),
		{'program_type':['specific',],'content_title':'Specific'}, name='prog-loc-report-specific'),

	url(r'^application-exception/$', views.ApplicationExceptionView.as_view(),
    	name='app-exp'),
  	url(r'^application-exception-ajax/$',
    	views.AEView.as_view(),name='app-exp-ajax'),

  	url(r'^deferred-docs-app/$',
    	views.DefDocsAppData.as_view(),name='deferred-docs-app'),
  	url(r'^deferred-docs-app-ajax/(?P<pg>\d+)/(?P<st>[\w\-\s\.\,]+)/(?P<adm_bat>[\w\-\s]+)$',
		views.DefDocsAppAjaxData.as_view(), name='def-doc-ajax'),

  	url(r'^deferred-docs-sub/$',
		views.DefDocsSubData.as_view(),name='deferred-docs-sub'),
	url(r'^deferred-docs-sub-ajax/(?P<pg>\d+)/(?P<st>[\w\-\s\.\,]+)/(?P<adm_bat>[\w\-\s]+)$',
		views.DefDocsSubAjaxData.as_view(), name='def-doc-sub-ajax'),

	url(r'^dmr_daily__certification/$',
		views.SubRev_DMRCertification.as_view(), name='dmr-daily-certification'),

	url(r'^dmr-daily-cluster/$',
		views.SubRev_DMRCluster.as_view(), name='dmr-daily-cluster'),

	url(r'^dmr-daily-specific/$',
		views.SubRev_DMRSpecific.as_view(), name='dmr-daily-specific'),

	url(r'^program-admissions-report/$',
		views.ProgramAdmissionsReport.as_view(), name='program-admissions-report'),
	
	url(r'^program-admissions-report-ajax/(?P<pg>\d+)/(?P<pg_type>[\w\-\s\.\,]+)/(?P<adm_btc>[\w\-\s]+)$',
		views.ProgramAdmissionsReportAjax.as_view(), name='program-admissions-report-ajax'
	 ),
]