from django.urls import path, include
from django.conf.urls import url
from master.ajax import views

app_name = 'ajax'

urlpatterns = [
path('set-qp-submissions-flag-ajax/', views.SetQPSubmissionsFlagAjax.as_view(), name='setqpsubmissionslockcheck'),
path('exam-slot/', views.ExamSlotAjax.as_view(), name='exam-slot'),
]