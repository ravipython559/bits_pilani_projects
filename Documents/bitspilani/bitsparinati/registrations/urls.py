"""
Registration Applicantion  URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from . import views, review_views
from django.contrib.auth.decorators import login_required
urlpatterns = [
    url(r'^saleforce/', include('registrations.saleforce.urls', namespace="saleforce")),
    url(r'^view-bitsrejectionreason',
     review_views.viewBitsRejectionReason,
     name="view-bitsrejectionreason"),
    url(r"^offer-letter-pdf/$", review_views.offerLetterRedirect,
        name="offer-letter"),
    url(r"offer-letter.pdf/$",review_views.OfferLetter.as_view(),
        name="offer-letter-pdf"),
    url(r'^pdf-offer-letter-redirect-direct-upload/$', review_views.pdf_redirect_direct_upload, 
        name="pdf-offer-letter-redirect-direct-upload"),

    url(r'^pdf-offer-letter-redirect-direct-upload1/$', review_views.pdf_redirect_direct_upload1, 
        name="pdf-offer-letter-redirect-direct-upload1"),

    url(r'^pay-fee-adm-view/$', review_views.AdmissionFeeView.as_view(), 
        name="pay-fee-adm"),
    url(r"^pay-admission-fee.pdf/$", login_required(review_views.Payfee.as_view()), 
        name="pay-admission-fee"),
    url(r'^admission-payment-error/$',
     views.admission_payment_error, name="admission-payment-error"),
	url(r'^send-confirmation-email/$',
		review_views.SendConfirmationRejectEmail.as_view(),
		name="send_confirmation_email"),
	url(r'^send-rejection-email/(?P<application_id>\d+)/$',
		review_views.send_rejection_email,
		name="send-rejection-email"),
	url(r'^recheck-send-rejection-email/$',
		review_views.recheck_send_rejection_email,
		name="recheck-send-rejection-email"),
	url(r'^recheck-send-confirmation-email/$',
		review_views.recheck_send_confirmation_email,
		name="recheck-send-confirmation-email"),
	url(r'^review-applicantion-details/(?P<application_id>\d+)/$',
		review_views.ReviewApplicationDetails.as_view(),
        name='review_application_details'),
	url(r'^review-applicant-data/$', review_views.RAData.as_view(),
		name="review-applicant-data"),
	url(r'^review-applicant-list/$', review_views.review_applicant_list,
		name="review-applicant-list"),
    url(r'^error-payment/$', views.payment_error, name="error-payment"),
    # url(r'registration-user/$', views.RegistrationViewUser.as_view(),
    #     name="registration-user"),
    url(r'^instruction-update/$', views.instruction_update_edit,
        name="instruction-update"),
    url(r'^payment-redirect/$', views.redirect_page, name="payment-redirect"),
    url(r'^bits-login/$', views.bits_login, name="bits-login"),
    url(r'^bits-login-admin/$', views.bits_admin_login,
        name="bits-login-admin"),
    url(r'^bits-login-user/$', views.bits_user_login, name="bits-login-user"),
    
    url(r"^payfeeview/$", views.getdata, name='payfeeview'),

    url(r'^view/$', views.view_data, name='applicantData'),
    url(r"^applicantView-pdf/$", views.finalPDFRedirect,
        name="applicantView"),
    url(r"applicantView.pdf/$", views.Applicant.as_view(),
        name="applicantViewPDF"),
    url(r"^reviewApplicantView.pdf/(?P<app_id>\w+)/$", views.ReviewApplicant.as_view(),
        name="reviewApplicantView"),
    url(r"^csvDownloadAdmin/$", views.csv_view),
    url(r'^feepage/$', views.fee_download_page, name="fee"),
    url(r"^payfee.pdf/$", 
    	login_required(views.Payfee.as_view()),
     name="payfee"),
    url(r"^studentapplication/(?P<pg_code>\w+)/$",
        views.application_form, name="student-application"),
    url(r"^studentapplication/source-site/(?P<pg_code>\w+)/(?P<source_site>\w+)/$",
        views.application_form, name="student-application-pg-source-site"),
    url(r"^studentapplicationEdit/$", views.application_form_edit,
        name="student-application-edit"),
    url(r"^studentapplicationViews/$", views.application_form_view,
        name="student-application-views"),
    url(r"^studentupload/$", views.StudentUpload.as_view(),
        name="student-upload"),
    url(r"^studentuploadedit/$", views.StudentUploadEdit.as_view(),
        name="student-upload-edit"),
    url(r"^ajax-mob/$", views.validatePhoneNumber,
        name="student-ajax-mob"),

    url(r"^studentUploadFileView/$", views.ConfirmationFile.as_view(),
        name="student-upload-file-view"),
    url(r"^instruction-user-login/$", views.user_login, name="user-login"),
    url(r"^uploadFinalFileDisplay/$", views.FinalUploadFile.as_view(),
        name="final-upload-file"),
    url(r'^applicant-data/$', views.applicant_data, name="applicant-data"),
    url(r'^pdf-redirect-direct-upload/$', views.pdf_redirect_direct_upload, name="pdf-redirect-direct-upload"),
    url(r"^instruction-user-waiver-login/$", views.user_waiver_login,
        name="user-waiver-login"),
    url(r'^reload-documentation/$',
        review_views.reload_documentation,
        name='reload-documentation'),
    url(r'^accept-offer/$', review_views.acceptOffer, name="accept-offer"),
    url(r'^accept-reject/$', review_views.acceptReject, name="accept-reject"),
    url(r'^payment-adm-redirect/$', review_views.redirect_page, name="payment-adm-redirect"),
    
    url(r'^refresh_applicant_data/$', review_views.review_program_location_refresh,
        name='refresh_applicant_data'),
    url(r'^fee-adm-page/$', review_views.fee_download_page, 
        name="fee-adm-page"),
    url(r"^ajax-email-id/$", views.validateEmailId,
        name="student-ajax-email-id"),

    url(r'^preview-offer-letter/(?P<app_id>\w+)/$',
        review_views.PreviewOfferLetter.as_view(), name="preview-offer-letter-pdf"),
    
    url(r'^offer-reviewer-redirect/(?P<app_id>\w+)/$',
        review_views.offerReviewerLetterRedirect, name="offer_reviewer_redirect"),
    url(r'^offer-reviewer-archived-redirect/(?P<pk>\d+)/$',
        review_views.archivedOfferReviewerLetterRedirect, name="archived_offer_reviewer_redirect"),

    url(r"^offer-letter-non-specific.pdf/(?P<app_id>\w+)/$",
     review_views.OfferLetterReviewerNonSpecific.as_view(), 
     name="offer-letter-non-specific-pdf"),
    url(r"^offer-letter-specific.pdf/(?P<app_id>\w+)/$",
     review_views.OfferLetterReviewerSpecific.as_view(), 
     name="offer-letter-specific-pdf"),

    url(r"^archived-offer-letter-non-specific.pdf/(?P<pk>\d+)/$",
     review_views.ArchivedOfferLetterReviewerNonSpecific.as_view(), 
     name="archived-offer-letter-non-specific-pdf"),
    url(r"^archived-offer-letter-specific.pdf/(?P<pk>\d+)/$",
     review_views.ArchivedOfferLetterReviewerSpecific.as_view(), 
     name="archived-offer-letter-specific-pdf"),

    url(r"^direct-url-for-application/(?P<pg_code>\w+)/$", views.direct_url_for_application,
        name="direct-url-for-application"),
    url(r"^verification-link-for-activation/(?P<activation_key>[-:\w]+)/(?P<pg_code>\w+)/$",
     views.verification_link_for_activation,
        name="verification-link-for-activation"),
    url(r"^verification-link-for-activation/(?P<activation_key>[-:\w]+)/(?P<pg_code>\w+)/(?P<source_site>\w+)/$",
     views.verification_link_for_activation,
        name="verification-link-for-activation-source-site"),
    url(r"^verification-link-for-activation-n/(?P<activation_key>[-:\w]+)/$",
     views.verification_link_for_activation,
        name="verification-link-for-activation-n"),
    url(r'^registration-user/$', views.RegistrationViewUser.as_view(),
        name="registration-user"),

    url(r"^ajax-mentor/(?P<pg_code>\w+)/$", views.validateMentor,
        name="student-ajax-mentor"),

    url(r'^qual-category-ajax/$', views.qualCategoryAjax,
        name="qual-category-ajax"),
    url(r'^qual-category-ajax/$', views.qualCategoryAjax1,
        name="qual-category-ajax1"),

    url(r'^createRCSV/$', review_views.RCSV.as_view(),
        name="createRCSV"),  #Change
    
    url(r'^choose-electives/$',views.ElectiveSelection.as_view(),
        name="choose-electives"),
    url(r'^choose-electives/(?P<status>\d)/$',views.ElectiveSelection.as_view(),
        name="choose-electives-with-alert-status"),

    url(r'^elective-ajax/',views.electiveAjax,
        name = 'elective-ajax'),

    url(r'^send_dob_details/(?P<pk>\d+)/$',
        review_views.SendDobDetails.as_view(),
        name='send_dob_details'),

    url(r'^pre_sel_rej_email/$',
        review_views.SendPreConfirmSelRejEmail.as_view(),
        name="pre_sel_rej_email"),
    url(r"^doc-create-or-update/$", views.ApplicationDocumentCreate.as_view(),
        name="doc-create"),
    url(r"^doc-create-or-update/(?P<pk>\d+)/$", views.ApplicationDocumentUpdate.as_view(),
        name="doc-update"),

    url(r'^doc-download-view/(?P<pk>\d+)/$', views.UserFileViewDownload.as_view(),
        name="document-view"),

    url(r'^doc-download-arch-view/(?P<pk>\d+)/$', views.UserArchivedFileViewDownload.as_view(),
        name="document-arch-view"),

]
