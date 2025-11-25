from rest_framework import serializers
from .models import Furgon

class FurgonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Furgon
        fields = "__all__"
