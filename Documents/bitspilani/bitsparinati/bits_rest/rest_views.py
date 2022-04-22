from rest_framework import viewsets, permissions, authentication
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_bulk import BulkModelViewSet
from .serializers import *
from .rest_authentication import ACAuthentication
from django.utils import timezone
from pytz import timezone as TZ
from registrations.models import *
from bits_admin.models import * 
from django.db.models import Q
from django.core.signing import TimestampSigner
from .rest_utils import authentication_classes, permission_classes, BoundTokenAuthentication
from .models import InBoundCall,  OutBoundCall
from registrations.utils import storage
import base64


class StandardResultsSetPagination(PageNumberPagination):
	page_size = 100
	page_size_query_param = 'page_size'
	max_page_size = 1000

class StudentCandidateMixin(object):
	## timestamp is considered to be utc always. 

	pg_code = None
	accepted_rejected_by_candidate = None
	authentication_classes = authentication_classes
	permission_classes = permission_classes
	pagination_class = StandardResultsSetPagination

	def list(self, *args, **kwargs):
		pg_code = kwargs.pop('pg_code', None)
		timestamp = kwargs.pop('timestamp', None)

		if timestamp == '00.00':
			timestamp = None

		if pg_code == 'all':
			pg_code = None

		self.pg_code = pg_code

		# self.accepted_rejected_by_candidate = (
		# 	timezone.datetime.utcfromtimestamp(
		# 		float(timestamp)
		# 	).replace(
		# 		tzinfo=TZ('UTC')
		# 	)
		# 	if timestamp else None
		# ) # fix me
		return super(StudentCandidateMixin, self).list(*args, **kwargs)

class CandidateSelectionViewSet(StudentCandidateMixin, viewsets.ReadOnlyModelViewSet):

	queryset = CandidateSelection.objects.exclude(
		Q(student_id='')|
		Q(student_id__isnull=True)
	)
	serializer_class = CandidateSelectionSerializer

	def get_queryset(self):
		self.queryset = (
			self.queryset.filter(
				application__program__program_code=self.pg_code,
			)
			if self.pg_code 
			else self.queryset
		)

		return self.queryset.filter(
			accepted_rejected_by_candidate__gte=self.accepted_rejected_by_candidate,
		) if self.accepted_rejected_by_candidate else self.queryset

class CandidateSelectionArchivedViewSet(StudentCandidateMixin, viewsets.ReadOnlyModelViewSet):

	queryset = CandidateSelectionArchived.objects.exclude(
		Q(student_id='')|
		Q(student_id__isnull=True)
	)
	serializer_class = CandidateSelectionArchivedSerializer

	def get_queryset(self):
		applications = StudentCandidateApplicationArchived.objects.filter(
			program=self.pg_code
		).values_list('student_application_id', flat=True)
		
		self.queryset = (
			self.queryset.filter(
				application__in=applications,
			)
			if self.pg_code 
			else self.queryset
		)

		return self.queryset.filter(
			accepted_rejected_by_candidate__gte=self.accepted_rejected_by_candidate,
		) if self.accepted_rejected_by_candidate else self.queryset

class ACAuthToken(ObtainAuthToken):
	
	serializer_class = UserSerializer

	def post(self, request, *args, **kwargs):

		serializer = self.serializer_class(data=request.data,context={'request': request})
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data['user']
		token, created = Token.objects.get_or_create(user=user)
		return Response({'token': token.key, 'email': user.email})

class InboundViewSet(viewsets.ModelViewSet):
	queryset = InBoundCall.objects.all()
	serializer_class = InBoundCallSerializer
	permission_classes = []
	authentication_classes = (BoundTokenAuthentication,)

class OutboundViewSet(viewsets.ModelViewSet):
	queryset = OutBoundCall.objects.all()
	serializer_class = OutBoundCallSerializer
	permission_classes = []
	authentication_classes = (BoundTokenAuthentication,)

class InboundBulkViewSet(BulkModelViewSet, InboundViewSet):
	serializer_class = InBoundCallBulkSerializer

	def allow_bulk_destroy(self, qs, filtered):
		return qs is not filtered

class OutboundBulkViewSet(BulkModelViewSet, OutboundViewSet):
	serializer_class = OutBoundCallBulkSerializer

	def allow_bulk_destroy(self, qs, filtered):
		return qs is not filtered

class HallTicketView(APIView):
	# permission_classes = []
	# authentication_classes = (BoundTokenAuthentication,)

	def get(self, request, student_id=None, format=None):
		try:
			historic_list = []
			historic_dict = {}
			historical_data = storage.document_extract_file(None, student_id)
			encoded_string = base64.b64encode(historical_data.read())
			historical_data = encoded_string.decode('utf-8')
			historic_dict['applicant_photo'] = historical_data
			historic_dict['file_name'] = ''.join(os.path.splitext(os.path.basename('documents/manual-upload/student-photo/{0}.jpg'.format(student_id))))
			historic_list.append(historic_dict)
			return Response({'ad':[], 'ad_arch': [], 'historical_data': historic_list})
		except:
			cs = CandidateSelection.objects.filter(student_id=student_id)
			ad = ApplicationDocument.objects.filter(
				application__in=cs.values_list('application', flat=True),
				document__document_name="APPLICANT PHOTOGRAPH",
			)
			cs_arch = CandidateSelectionArchived.objects.filter(student_id=student_id)
			ad_arch = ApplicationDocumentArchived.objects.filter(
				application__in=cs_arch.values_list('application', flat=True),
				document="APPLICANT PHOTOGRAPH",
			)
			ad_serializer = ApplicationDocumentSerializer(ad, many=True, context={'request': request})
			ad_arch_serializer = ApplicationDocumentArchivedSerializer(ad_arch, many=True, context={'request': request})
			historic_list = []
			return Response({'ad':ad_serializer.data, 'ad_arch': ad_arch_serializer.data, 'historical_data': historic_list})

class AgentAuthToken(ObtainAuthToken):
	serializer_class = AgentSerializer

	def post(self, request, *args, **kwargs):
		serializer = self.serializer_class(data=request.data, context={'request': request})
		serializer.is_valid(raise_exception=True)
		agent = serializer.validated_data['agent']
		signer = TimestampSigner()
		return Response({'token': signer.sign(agent.key)})