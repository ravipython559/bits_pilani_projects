from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from registrations.models import *
from bits_admin.models import *
from .models import (
	InBoundProgramInterested, InBoundPhone, InBoundQuery, InBoundVOC, 
	InBoundCall, OutBoundProgramInterested, OutBoundPhone, 
	OutBoundQuery, OutBoundVOC, OutBoundCall, Agent,
)
from django.db import transaction
from .serializers_fields import SCAArchivedKeyRelatedField, SCAKeyRelatedField
from django.contrib.auth.hashers import check_password

from rest_framework_bulk import (BulkListSerializer, BulkSerializerMixin,)
from rest_framework import ISO_8601
from registrations.utils import storage
import base64
import os

DATETIME_INPUT_FORMATS = (
	ISO_8601,
	'%d/%m/%Y %H:%M:%S',
	'%d/%m/%Y %H:%M:%S.%f',
	'%d-%m-%Y %H:%M:%S',
	'%d-%m-%Y %H:%M:%S.%f',
	'%d/%m/%y %H:%M:%S',
	'%d/%m/%y %H:%M:%S.%f',
	'%d-%m-%y %H:%M:%S',
	'%d-%m-%y %H:%M:%S.%f',
	
)

class StudentCandidateApplicationSerializer(serializers.ModelSerializer):
	login_email = serializers.ReadOnlyField(source='login_email.email')
	program = serializers.ReadOnlyField(source='program.program_code')
	current_location = serializers.ReadOnlyField(source='current_location.location_name')
	current_org_industry = serializers.ReadOnlyField(source='current_org_industry.industry_name')
	work_location = serializers.ReadOnlyField(source='work_location.location_name')
	
	class Meta:
		model = StudentCandidateApplication
		fields = '__all__'

class CandidateSelectionSerializer(serializers.ModelSerializer):
	sca = SCAKeyRelatedField(
		source='application',
		default=StudentCandidateApplicationSerializer,
		queryset=StudentCandidateApplication.objects.all(),
	)
	rejection_by_candidate_reason = serializers.ReadOnlyField(source='rejection_by_candidate_reason.reason')
	new_sel_prog = serializers.ReadOnlyField(source='new_sel_prog.program_code')
	admitted_to_program = serializers.ReadOnlyField(source='admitted_to_program.program_code')
	
	class Meta:
		model = CandidateSelection
		fields = '__all__'

class StudentCandidateApplicationArchivedSerializer(serializers.ModelSerializer):

	class Meta:
		model = StudentCandidateApplicationArchived
		fields = '__all__'

class CandidateSelectionArchivedSerializer(serializers.ModelSerializer):

	sca = SCAArchivedKeyRelatedField(
		source='pk',
		queryset=StudentCandidateApplicationArchived.objects.all(),
		default=StudentCandidateApplicationArchivedSerializer,
	)

	class Meta:
		model = CandidateSelectionArchived
		fields = '__all__'

class UserSerializer(serializers.Serializer):
	email = serializers.CharField(label=_("Email"))

	def validate(self, attrs):
		email = attrs.get('email')

		if email:
			user = authenticate(email=email)

			if user:
				if not user.is_superuser:
					msg = _('User account is not superuser.')
					raise serializers.ValidationError(msg)
			else:
				msg = _('Unable to log in with provided credentials.')
				raise serializers.ValidationError(msg)
		else:
			msg = _('Must include "email" and "password".')
			raise serializers.ValidationError(msg)

		attrs['user'] = user
		return attrs

#inbound serializer
class InBoundProgramInterestedSerializer(serializers.ModelSerializer):
	class Meta:
		model = InBoundProgramInterested
		exclude = ('bound',)

class InBoundPhoneSerializer(serializers.ModelSerializer):
	class Meta:
		model = InBoundPhone
		exclude = ('bound',)

class InBoundQuerySerializer(serializers.ModelSerializer):
	class Meta:
		model = InBoundQuery
		exclude = ('bound',)

class InBoundVOCSerializer(serializers.ModelSerializer):
	class Meta:
		model = InBoundVOC
		exclude = ('bound',)

class InBoundCallSerializer(serializers.ModelSerializer):
	inboundprograminterested_bound = InBoundProgramInterestedSerializer(many=True)
	inboundphone_bound = InBoundPhoneSerializer(many=True)
	inboundquery_bound = InBoundQuerySerializer(many=True)
	inboundvoc_bound = InBoundVOCSerializer(many=True)

	class Meta:
		model = InBoundCall
		exclude = ('created_on','application',)
		extra_kwargs = {'called_on':{'input_formats':DATETIME_INPUT_FORMATS}}

	def create(self, validated_data):
		program_interested = validated_data.pop('inboundprograminterested_bound')
		phone = validated_data.pop('inboundphone_bound')
		query = validated_data.pop('inboundquery_bound')
		voc = validated_data.pop('inboundvoc_bound')

		with transaction.atomic():

			bound = InBoundCall.objects.create(**validated_data)

			InBoundProgramInterested.objects.bulk_create(
				[ 
					InBoundProgramInterested(bound=bound, **d) for d in program_interested
				]
			)
			for d in phone:
				InBoundPhone.objects.create(bound=bound, **d)

			# InBoundPhone.objects.bulk_create([InBoundPhone(bound=bound, **d) for d in phone])
			InBoundQuery.objects.bulk_create([InBoundQuery(bound=bound, **d) for d in query])
			InBoundVOC.objects.bulk_create([InBoundVOC(bound=bound, **d) for d in voc])

		return bound

# outbound call serializer
class OutBoundProgramInterestedSerializer(serializers.ModelSerializer):
	class Meta:
		model = OutBoundProgramInterested
		exclude = ('bound',)

class OutBoundPhoneSerializer(serializers.ModelSerializer):
	class Meta:
		model = OutBoundPhone
		exclude = ('bound',)

class OutBoundQuerySerializer(serializers.ModelSerializer):
	class Meta:
		model = OutBoundQuery
		exclude = ('bound',)

class OutBoundVOCSerializer(serializers.ModelSerializer):
	class Meta:
		model = OutBoundVOC
		exclude = ('bound',)

class OutBoundCallSerializer(serializers.ModelSerializer):
	outboundphone_bound = OutBoundPhoneSerializer(many=True)
	outboundquery_bound = OutBoundQuerySerializer(many=True)
	outboundvoc_bound = OutBoundVOCSerializer(many=True)
	outboundprograminterested_bound = OutBoundProgramInterestedSerializer(many=True)

	class Meta:
		model = OutBoundCall
		exclude = ('created_on','application',)
		extra_kwargs = {'called_on':{'input_formats':DATETIME_INPUT_FORMATS}}

	def create(self, validated_data):
		program_interested = validated_data.pop('outboundprograminterested_bound')
		phone = validated_data.pop('outboundphone_bound')
		query = validated_data.pop('outboundquery_bound')
		voc = validated_data.pop('outboundvoc_bound')

		with transaction.atomic():

			bound = OutBoundCall.objects.create(**validated_data)

			OutBoundProgramInterested.objects.bulk_create(
				[ 
					OutBoundProgramInterested(bound=bound, **d) for d in program_interested
				]
			)
			for d in phone:
				OutBoundPhone.objects.create(bound=bound, **d)
			# OutBoundPhone.objects.bulk_create([OutBoundPhone(bound=bound, **d) for d in phone])
			OutBoundQuery.objects.bulk_create([OutBoundQuery(bound=bound, **d) for d in query])
			OutBoundVOC.objects.bulk_create([OutBoundVOC(bound=bound, **d) for d in voc])

		return bound


class AgentSerializer(serializers.Serializer):
	username = serializers.CharField(label='username')
	password = serializers.CharField(label='password')

	def validate(self, attrs):
		username = attrs.get('username')
		password = attrs.get('password')

		if username:
			try:
				agent = Agent.objects.get(username=username)
			except Agent.DoesNotExist:
				raise serializers.ValidationError('Authentication Failed. User does not exist.')

			if not check_password(password, agent.password):
				raise serializers.ValidationError('incorrect credentials.')
		else:
			raise serializers.ValidationError('username and password required for authentication.')

		attrs['agent'] = agent

		return attrs

class InBoundCallBulkSerializer(BulkSerializerMixin, InBoundCallSerializer):
	class Meta(InBoundCallSerializer.Meta):
		list_serializer_class = BulkListSerializer

class OutBoundCallBulkSerializer(BulkSerializerMixin, OutBoundCallSerializer):
	class Meta(OutBoundCallSerializer.Meta):
		list_serializer_class = BulkListSerializer


class ApplicationDocumentSerializer(serializers.ModelSerializer):
	
	application = StudentCandidateApplicationSerializer()
	file_name = serializers.SerializerMethodField()
	applicant_photo = serializers.SerializerMethodField()

	def get_file_name(self, obj):
		return ''.join(os.path.splitext(os.path.basename(obj.file.name)))

	def get_applicant_photo(self, obj):
		temp_file = storage.document_extract_file(obj)
		encoded_string = base64.b64encode(temp_file.read())
		return encoded_string.decode('utf-8')
	
	
	class Meta:
		model = ApplicationDocument
		fields = '__all__'

class ApplicationDocumentArchivedSerializer(serializers.ModelSerializer):

	application = StudentCandidateApplicationArchivedSerializer()
	file_name = serializers.SerializerMethodField()
	applicant_photo = serializers.SerializerMethodField()

	def get_file_name(self, obj):
		return ''.join(os.path.splitext(os.path.basename(obj.file.name)))

	def get_applicant_photo(self, obj):
		temp_file = storage.document_extract_file(obj)
		encoded_string = base64.b64encode(temp_file.getvalue())
		return encoded_string.decode('utf-8')

	class Meta:
		model = ApplicationDocumentArchived
		fields = '__all__'
