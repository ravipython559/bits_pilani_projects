from django.urls import path,include
from django.conf.urls import include, url
from . import views

app_name = 'administrator'

urlpatterns = [
		url(r'^qp_submission_status_view/$', views.QPSubmissionStatusView.as_view(), name='qp_submission_status_view'),
		url(r'^qp_submission_status_ajax_view/(?P<data>.*)/$', views.QPSubmissionStatusAjaxView.as_view(), name='qp_submission_status_ajax_view'),
		url(r'^qp_submissions_download_view/$', views.QPSubmissionsDownloadView.as_view(), name='qp_submissions_download_view'),
		url(r'^qp_submissions_download_ajax_view/(?P<data>.*)/$', views.QPSubmissionsDownloadAjaxView.as_view(), name='qp_submissions_download_ajax_view'),
		url(r'^sync-ema-examtype/$', views.SyncEMAExamtype.as_view(), name='sync-ema-examtype'),
		url(r'^sync-ema-batch/$', views.SyncEMABatch.as_view(), name='sync-ema-batch'),
		url(r'^sync-ema-semester/$', views.SyncEMASemester.as_view(), name='sync-ema-semester'),
		url(r'^sync-ema-examslot/$', views.SyncEMAExamSlot.as_view(), name='sync-ema-examslot'),
		path('qp_path_view_details/<int:pk>/', views.QPPathViewDetailsView.as_view(), name='qp_path_view_details'),
		#file-viewing-downoad
		path('doc-download-view/<int:pk>/<str:storage_path>', views.adminUserFileViewDownload.as_view(),name="document-view"),
		path('manage-qp-lock-unlock/', views.ManageQPLockUnlockView.as_view(), name='manage_qp_lock_unlock'),
		path('course-ajax/', views.get_course_detail, name='course_ajax'),
		path('multi-doc-download-view/', views.multidocdownloadview,name="multi-doc-download-view"),
		url(r'^multi_download_ajax_view/$', views.multi_download_ajax_view, name='multi_download_ajax_view'),
]