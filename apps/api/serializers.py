from rest_framework import serializers
from apps.data.models.registry.nothospitalized import PatientRegistry


class PatientRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientRegistry
        fields = '__all__'
