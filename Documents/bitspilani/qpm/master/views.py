from django.views.generic import View,FormView,TemplateView,UpdateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, FileResponse
from django.http import HttpResponseNotFound
import io
import magic
from .models import *
from django.conf import settings
from master.utils.storage import *

@method_decorator([login_required, never_cache,], name='dispatch')
class UserFileViewDownload(View):

	def get_application_document(self, request, pk):
		pass

	def get(self, request, pk,storage_path, *args, **kwargs):

		QP_doc = self.get_application_document(request, pk)
		if QP_doc:
			if storage_path=='qp_path':
				temp_file = document_extract_file(QP_doc.qp_path.name)
			elif storage_path=='alternate_qp_path':
				temp_file = document_extract_file(QP_doc.alternate_qp_path.name)

			content = temp_file.read()
			mime_type = magic.from_buffer(temp_file.getvalue(), mime=True)
			response = HttpResponse(temp_file.getvalue(), content_type=mime_type)
			if storage_path=='qp_path':
				if mime_type =='application/vnd.openxmlformats-officedocument.wordprocessingml.document' or os.path.splitext(QP_doc.qp_path.name)[1].lower()=='.docx':
					response['Content-Disposition'] = 'attachment; filename = "download.docx"'
					response['Content-Type'] = "application/octet-stream"
			elif storage_path=='alternate_qp_path':
				if mime_type =='application/vnd.openxmlformats-officedocument.wordprocessingml.document' or os.path.splitext(QP_doc.alternate_qp_path.name)[1].lower()=='.docx':
					response['Content-Disposition'] = 'attachment; filename = "download.docx"'
					response['Content-Type'] = "application/octet-stream"

			return response
		else:
			return HttpResponseNotFound("<h5>You don't have access to this Files</h5>")

class unauthorised(TemplateView):
	template_name = 'master/403.html'
