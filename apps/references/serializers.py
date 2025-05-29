from rest_framework import serializers
from .models import MKB10, InsuranceCompany

class MKB10Serializer(serializers.ModelSerializer):
    parent_code = serializers.CharField(source='parent.code', read_only=True)
    children_count = serializers.IntegerField(read_only=True)
    full_path = serializers.CharField(read_only=True)

    class Meta:
        model = MKB10
        fields = [
            'id', 'code', 'name', 'parent', 'parent_code',
            'level', 'is_active', 'description', 'children_count',
            'full_path', 'created_at', 'updated_at'
        ]
        read_only_fields = ['level', 'created_at', 'updated_at']

class MKB10TreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = MKB10
        fields = ['id', 'code', 'name', 'children']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return MKB10TreeSerializer(children, many=True).data

class InsuranceCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceCompany
        fields = '__all__' 