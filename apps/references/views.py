from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, filters, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import MKB10
from .serializers import MKB10Serializer, MKB10TreeSerializer
from django.db import models

# Create your views here.

class MKB10ViewSet(viewsets.ModelViewSet):
    queryset = MKB10.objects.all()
    serializer_class = MKB10Serializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'level']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'level', 'created_at']
    ordering = ['code']

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('parent')

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Получить дерево диагнозов"""
        root_items = MKB10.objects.filter(parent=None, is_active=True)
        serializer = MKB10TreeSerializer(root_items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Получить дочерние элементы диагноза"""
        diagnosis = self.get_object()
        children = diagnosis.children.filter(is_active=True)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

class MKB10ListView(generics.ListAPIView):
    """
    API для получения списка кодов МКБ-10.
    
    Параметры запроса:
    - search: поиск по коду или названию
    - level: фильтр по уровню (1 - категории, 2 - подкатегории)
    - is_active: фильтр по активности (true/false)
    - is_final: фильтр по конечным диагнозам (true/false)
    """
    serializer_class = MKB10Serializer
    
    def get_queryset(self):
        queryset = MKB10.objects.all()
        
        # Поиск
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(code__icontains=search) |
                models.Q(name__icontains=search)
            )
        
        # Фильтр по уровню
        level = self.request.query_params.get('level', None)
        if level:
            queryset = queryset.filter(level=level)
        
        # Фильтр по активности
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        # Фильтр по конечным диагнозам
        is_final = self.request.query_params.get('is_final', None)
        if is_final is not None:
            queryset = queryset.filter(is_final=is_final.lower() == 'true')
        
        return queryset.select_related('parent')


class MKB10DetailView(generics.RetrieveAPIView):
    """
    API для получения детальной информации о коде МКБ-10.
    
    Параметры URL:
    - code: код МКБ-10 (например, A00.0)
    """
    serializer_class = MKB10Serializer
    
    def get_object(self):
        code = self.kwargs['code']
        return get_object_or_404(MKB10, code=code)


class MKB10ChildrenView(generics.ListAPIView):
    """
    API для получения дочерних кодов МКБ-10.
    
    Параметры URL:
    - code: код МКБ-10 (например, A00)
    """
    serializer_class = MKB10Serializer
    
    def get_queryset(self):
        code = self.kwargs['code']
        parent = get_object_or_404(MKB10, code=code)
        return MKB10.objects.filter(parent=parent).select_related('parent')
