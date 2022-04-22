from django.conf.urls import url
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
url(r'application-specific-form-add/(?P<pg_code>\w+)/$',
     views.application_form,
     name='specific_form_add'),
url(r'application-specific-edit-form-add/$',
     views.application_form_edit,
     name='specific_edit_form_add'),
url(r'specific-user-program/$',
     views.user_specific_login,
     name='specific_user_program'),
url(r'student-upload-form/$',
     views.StudentUpload.as_view(),
     name='student_upload_form'),
url(r'student-upload-form-edit/$',
     views.StudentUploadEdit.as_view(),
     name='student_upload_form_edit'),
url(r'upload-file-view/$',
     views.ConfirmationFile.as_view(),
     name='upload_file_view'),

url(r'final-upload-file/$',
     views.FinalUploadFile.as_view(),
     name='final_upload_file'),

url(r'application-form-view/$',
     views.application_form_view,
     name='application_form_view'),

url(r'specific-student-pdf/$',
     views.pdf_redirect_direct_upload,
     name='pdf_redirect_direct_upload'),

url(r"applicantView-pdf/$", views.finalUploadFile1,
        name="applicantView"),
url(r"applicantView.pdf/$", views.Applicant.as_view(),
        name="applicantViewPDF"),

url(r"offer-letter.pdf/$", views.OfferLetter.as_view(),
        name="specific-offer-letter"),

url(r'reload-documentation/$',
        views.reload_documentation,
        name='reload-documentation'),

]