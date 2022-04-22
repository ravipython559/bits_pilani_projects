from django.urls import path
from django.conf.urls import include, url
from . import views

app_name = 'coordinator'
urlpatterns = [
				path('qp_submission_status_view/', views.QPSubmissionStatusView.as_view(), name='qp_submission_status_view'),
				url(r'^coord_qp_submission_status_ajax_view/(?P<data>.*)/$', views.QPSubmissionStatusAjaxView.as_view(), name='coord_qp_submission_status_ajax_view'),
				path('home', views.Home.as_view(), name='index'),
				path('QP-update/<int:pk>/', views.qp_update.as_view(), name='qp_update'),
				path('QP-submission-status/', views.qp_submision_status.as_view(), name='qp_submission_status'),
				path('doc-download-view/<int:pk>/<str:storage_path>', views.coordinatorUserFileViewDownload.as_view(),name="document-view"),

]
