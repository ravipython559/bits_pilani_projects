from django.urls import path, include
from django.conf.urls import url
from . import views

app_name = 'faculty'
urlpatterns = [
			path('home', views.Home.as_view(), name='index'),
			path('QP-update/<int:pk>/', views.qp_update.as_view(), name='qp_update'),
			path('QP-submission-status/', views.qp_submision_status.as_view(), name='qp_submission_status'),
			url(r'^fac_qp_submission_status_ajax_view/(?P<data>.*)/$', views.FacQPSubmissionStatusAjaxView.as_view(), name='fac_qp_submission_status_ajax_view'),
			#ajax-urls
			path('semester_drop_down-ajax', views.semester_drop_down.as_view(),name='semester_drop_down'),
			path('batch_drop_down-ajax', views.batch_drop_down.as_view(),name='batch_drop_down'),
			path('course_drop_down-ajax', views.course_drop_down.as_view(),name='course_drop_down'),
			path('get-program-slot-ajax', views.get_program_examslot.as_view(),name='get-program-slot'),

			#file-viewing-downoad
			path('doc-download-view/<int:pk>/<str:storage_path>', views.FacultyUserFileViewDownload.as_view(),name="document-view"),
]
