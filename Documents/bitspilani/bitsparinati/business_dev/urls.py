from django.conf.urls import url, include
from . import views


urlpatterns = [
	url(r'^ajax_data/(?P<pg>\d+)/(?P<st>[\w\-\s\.\,]+)/(?P<fm_dt>[\d\-\:\s]+)/(?P<to_dt>[\d\-\:\s]+)/(?P<pg_typ>[\w\-\s]+)/(?P<adm_bat>[\w\-\s]+)$',
     views.MyDataView.as_view(), name='table_data'),
	url(r'^home/',views.ViewData.as_view(),
        name='applicantData'),
	url(r'^dateFormat/$',views.DateRefresh.as_view(),
        name='dateFormat'),
	url(r'^createcsv/$',views.CSVView.as_view(),
        name='createCSV'),

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
  url(r'business-application-details/(?P<application_id>\d+)/$',
    views.ApplicantDetail.as_view(),
    name='business_application_details'),

    url(r'^archive-data-view/$',views.ArchiveHomeDataView.as_view(),
        name='archive-data-view'),
    url(r'^ajax_archive_data/(?P<pg>\d+)/(?P<st>[\w\-\s\.\,]+)/(?P<fm_dt>[\d\-\:\s]+)/(?P<to_dt>[\d\-\:\s]+)/(?P<pg_typ>[\w\-\s]+)/(?P<adm_bat>[\w\-\s]+)$',
     views.ArchiveDataView.as_view(), name='table_archive_data'),
    url(r'^postArchApp/$',views.FilterArchivalApplicant.as_view(),
        name='postArchApp'),
    url(r'^adminapplicationarchiveViews/(?P<pk>\d+)/(?P<run_id>\d+)/$', 
        views.ApplicationAdminArchiveView.as_view(),
        name="admin-application-archive-views"),
    url(r'^createarchivecsv/$',views.CSVArchiveView.as_view(),
        name='createArchiveCSV'),

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

  url(r'^emi-report/$',
    views.EMIReportAppData.as_view(),name='emi-report'),
  url(r'^emi-report-ajax/(?P<pg>\d+)/(?P<b_id>[\d\-\s]+)/(?P<st>[\w\-\s\.\,]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
    views.EMIReportAppAjaxData.as_view(), name='emi-report-ajax'),

  url(r'^dmr_daily__certification/$',
     views.BD_DMRCertification.as_view(), name='dmr-daily-certification'),
  url(r'^dmr-daily-cluster/$',
     views.BD_DMRCluster.as_view(), name='dmr-daily-cluster'),
  url(r'^dmr-daily-specific/$',
     views.BD_DMRSpecific.as_view(), name='dmr-daily-specific'),


  url(r'^program-admissions-report/$',
    views.ProgramAdmissionsReport.as_view(), name='program-admissions-report'),
  url(r'^program-admissions-report-ajax/(?P<pg>\d+)/(?P<pg_type>[\w\-\s\.\,]+)/(?P<adm_btc>[\w\-\s]+)$',
    views.ProgramAdmissionsReportAjax.as_view(), name='program-admissions-report-ajax'
   ),

  url(r'^emi-report-eduv/$',
    views.EMIReportEduvAppData.as_view(),name='emi-report-eduv'),
  url(r'^emi-report-eduv-ajax/(?P<pg>\d+)/(?P<b_id>[\d\-\s]+)/(?P<st>[\w\-\s\.\,]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
    views.EMIReportEduvAppAjaxData.as_view(), name='emi-report-eduv-ajax'),

  url(r'^emi-report-ezcred/$',
    views.EMIReportEzcredAppData.as_view(),name='emi-report-ezcred'),
  url(r'^emi-report-ezcred-ajax/(?P<pg>\d+)/(?P<b_id>[\d\-\s]+)/(?P<st>[\w\-\s\.\,]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
    views.EMIReportEzcredAppAjaxData.as_view(), name='emi-report-ezcred-ajax'),

    url(r'^emi-report-propelld/$',
    views.EMIReportPropelldAppData.as_view(),name='emi-report-propelld'),
  url(r'^emi-report-propelld-ajax/(?P<pg>\d+)/(?P<b_id>[\d\-\s]+)/(?P<st>[\w\-\s\.\,]+)/(?P<p_type>[\w\-\s\.\,]+)/$',
    views.EMIReportPropelldAppAjaxData.as_view(), name='emi-report-propelld-ajax'),

]