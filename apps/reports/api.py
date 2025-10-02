from rest_framework import serializers, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q

from .models import DeleteEmd, InvalidationReason, MedicalOrganizationOMSTarget
from apps.organization.models import MedicalOrganization


class DeleteEmdSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    status_color = serializers.CharField(source='get_status_color', read_only=True)
    oid_medical_organization_name = serializers.CharField(source='oid_medical_organization.name', read_only=True)
    reason_not_actual_text = serializers.CharField(source='reason_not_actual.reason_text', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = DeleteEmd
        fields = '__all__'
        extra_kwargs = {
            'created_by': {'required': False},
            'added_date': {'required': False},
            'responsible': {'required': False},
        }

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.can_edit(request.user)
        return False

    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.can_delete(request.user)
        return False


class DeleteEmdViewSet(viewsets.ModelViewSet):
    queryset = DeleteEmd.objects.all()
    serializer_class = DeleteEmdSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_superuser:
            return DeleteEmd.objects.all().order_by('-updated_at')
        elif user.is_authenticated:
            # Поддерживаем текстовое поле responsible (сравнение по ФИО/логину)
            user_full_name = user.get_full_name() or ''
            return DeleteEmd.objects.filter(
                Q(created_by=user) |
                Q(responsible__iexact=user_full_name) |
                Q(responsible__iexact=user.username)
            ).distinct().order_by('-updated_at')
        else:
            # Для неаутентифицированных пользователей показываем все записи
            return DeleteEmd.objects.all().order_by('-updated_at')
    
    def perform_create(self, serializer):
        # Определяем создателя: аутентифицированный пользователь или первый суперюзер/"admin"
        request_user = self.request.user
        if request_user.is_authenticated:
            creator = request_user
        else:
            creator = User.objects.filter(is_superuser=True).first() or User.objects.filter(username='admin').first()
        # Ответственный: используем переданное текстовое значение или ФИО/логин создателя, либо 'admin'
        responsible_value = serializer.validated_data.get('responsible')
        if not responsible_value:
            if creator:
                responsible_value = creator.get_full_name() or creator.username or 'admin'
            else:
                responsible_value = 'admin'

        serializer.save(
            created_by=creator,
            responsible=responsible_value
        )
    
    def perform_update(self, serializer):
        # При обновлении не изменяем created_by и added_date
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Изменение статуса заявки"""
        instance = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(DeleteEmd.STATUS_CHOICES):
            return Response({'error': 'Неверный статус'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем права на изменение статуса
        if not (request.user.is_superuser or request.user == instance.responsible):
            return Response({'error': 'Нет прав на изменение статуса'}, status=status.HTTP_403_FORBIDDEN)
        
        instance.status = new_status
        instance.save()
        
        return Response({'status': 'Статус изменен', 'new_status': instance.get_status_display()})
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Получить заявки текущего пользователя"""
        queryset = self.get_queryset().filter(created_by=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_responsible(self, request):
        """Получить заявки, где пользователь ответственный"""
        queryset = self.get_queryset().filter(responsible=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class InvalidationReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvalidationReason
        fields = '__all__'


class InvalidationReasonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InvalidationReason.objects.all()
    serializer_class = InvalidationReasonSerializer


class MedicalOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalOrganization
        fields = ['id', 'name']


class MedicalOrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MedicalOrganization.objects.all()
    serializer_class = MedicalOrganizationSerializer


class MedicalOrganizationOMSTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalOrganizationOMSTarget
        fields = ['id', 'name']


class MedicalOrganizationOMSTargetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MedicalOrganizationOMSTarget.objects.filter(is_active=True)
    serializer_class = MedicalOrganizationOMSTargetSerializer


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name']


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
