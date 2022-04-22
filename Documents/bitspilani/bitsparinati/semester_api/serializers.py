from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

class ZestCreateSerializer(serializers.Serializer):
	email = serializers.CharField(label=_("Email"))
	student_id = serializers.CharField(label=_("Student Id"))
	pincode = serializers.CharField(label=_("Pincode"))
	basket_amount = serializers.CharField(label=_("Basket Amount"))
	mobile = serializers.CharField(label=_("Mobile"))
	key = serializers.CharField(label=_("Key"))

class StudentIDSerializer(serializers.Serializer):
	student_id = serializers.CharField(label=_("Student Id"))