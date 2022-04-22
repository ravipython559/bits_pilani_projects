from easy_pdf.views import PDFTemplateView
from easy_pdf.rendering import render_to_pdf_response


class BasePDFTemplateView(PDFTemplateView):
	def get_pdf_response(self, context, **response_kwargs):
		return render_to_pdf_response(
			request=self.request,
			template=self.get_template_names(),
			context=context,
			filename=self.get_pdf_filename(),
			encoding="utf-8",
		)