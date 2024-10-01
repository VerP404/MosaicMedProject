from dal import autocomplete
from django.http import JsonResponse
from .models import *
from ..organization.models import *


class SpecialtyAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return SpecialtyRG014.objects.none()

        qs = SpecialtyRG014.objects.all()

        if self.q:
            qs = qs.filter(description__icontains=self.q)

        return qs


class PostAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return PostRG014.objects.none()

        qs = PostRG014.objects.all()

        if self.q:
            qs = qs.filter(description__icontains=self.q)

        return qs


class DepartmentAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Department.objects.none()

        qs = Department.objects.all()

        # Фильтрация по корпусу (параметр 'building' должен быть передан в GET-запросе)
        building_id = self.forwarded.get('building', None)
        if building_id:
            qs = qs.filter(building_id=building_id)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs
