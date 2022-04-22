from rest_framework.relations import RelatedField
from rest_framework import serializers
from registrations.models import *
from bits_admin.models import *

class SCAArchivedKeyRelatedField(RelatedField):

	def to_representation(self, value):
		cs = CandidateSelectionArchived.objects.get(pk=value)
		try:
			query = self.get_queryset().filter(
				student_application_id=cs.application, 
				run=cs.run
			)
		except StudentCandidateApplicationArchived.DoesNotExist as e:
			return None
		return self.default(query.last()).data

class SCAKeyRelatedField(serializers.PrimaryKeyRelatedField):

	def to_representation(self, value):
		query = self.get_queryset().get(pk=value.pk)
		return self.default(query).data

# # use the below code for testing perpose


# from rest_framework.request import Request
# from rest_framework.test import APIRequestFactory
# from bits_rest.serializers import *
# factory = APIRequestFactory()
# request = factory.get('/')


# serializer_context = {
#     'request': Request(request),
# }

# p = CandidateSelection.objects.all()
# s = CandidateSelectionSerializer(p, context=serializer_context, many=True)

# print s.data