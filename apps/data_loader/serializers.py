# serializers.py
from rest_framework import serializers

from apps.data_loader.models.oms_data import OMSData


class OMSDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = OMSData
        fields = '__all__'
