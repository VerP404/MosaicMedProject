from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import BenefitCategory, Patient, Drug, PatientDrugSupply, DrugStock
from apps.load_data.models import Recipe


@login_required
def beneficiaries_home_view(request):
    """Главная страница системы льготников"""
    # Статистика
    total_patients = Patient.objects.filter(is_active=True).count()
    total_categories = BenefitCategory.objects.filter(is_active=True).count()
    total_drugs = Drug.objects.filter(is_active=True).count()
    total_recipes = Recipe.objects.count()
    
    # Срочные и истекшие
    today = timezone.now().date()
    urgent = PatientDrugSupply.objects.filter(
        supplied_until__lte=today + timedelta(days=7),
        supplied_until__gte=today,
        status='active'
    ).count()
    
    expired = PatientDrugSupply.objects.filter(
        supplied_until__lt=today,
        status='active'
    ).count()
    
    context = {
        'page_title': 'Система льготников',
        'total_patients': total_patients,
        'total_categories': total_categories,
        'total_drugs': total_drugs,
        'total_recipes': total_recipes,
        'urgent_supplies': urgent,
        'expired_supplies': expired,
    }
    return render(request, 'beneficiaries/home.html', context)


@login_required
def beneficiaries_list_view(request):
    """Главная страница с таблицей льготников"""
    return render(request, 'beneficiaries/beneficiaries_list.html', {
        'page_title': 'Льготники',
    })


@login_required
def patient_detail_view(request, patient_id):
    """Детальная информация о пациенте-льготнике"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    context = {
        'page_title': f'Пациент: {patient.full_name}',
        'patient': patient,
    }
    return render(request, 'beneficiaries/patient_detail.html', context)


@login_required
@require_http_methods(["GET"])
def beneficiaries_list_api(request):
    """API для получения списка льготников"""
    try:
        # Параметры фильтрации
        category_id = request.GET.get('category')
        is_children = request.GET.get('is_children')
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', 'active')  # active, all
        
        # Базовый запрос
        patients_query = Patient.objects.select_related('benefit_category').prefetch_related(
            Prefetch('drug_supplies', queryset=PatientDrugSupply.objects.select_related('drug'))
        )
        
        # Фильтры
        if status == 'active':
            patients_query = patients_query.filter(is_active=True)
        
        if category_id:
            patients_query = patients_query.filter(benefit_category_id=category_id)
        
        if is_children == 'true':
            patients_query = patients_query.filter(benefit_category__is_for_children=True)
        elif is_children == 'false':
            patients_query = patients_query.filter(benefit_category__is_for_children=False)
        
        if search:
            patients_query = patients_query.filter(
                Q(full_name__icontains=search) |
                Q(snils__icontains=search) |
                Q(enp__icontains=search) |
                Q(diagnosis_code__icontains=search)
            )
        
        # Пагинация
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
        
        paginator = Paginator(patients_query, page_size)
        patients_page = paginator.get_page(page)
        
        # Формируем данные
        patients_data = []
        for patient in patients_page:
            # Получаем препараты пациента
            drug_supplies = patient.drug_supplies.all()
            
            # Считаем количество препаратов с разными статусами
            active_drugs = drug_supplies.filter(status='active').count()
            urgent_drugs = sum(1 for supply in drug_supplies if supply.is_urgent)
            expired_drugs = sum(1 for supply in drug_supplies if supply.is_expired)
            
            patients_data.append({
                'id': patient.id,
                'full_name': patient.full_name,
                'birth_date': patient.birth_date.strftime('%d.%m.%Y'),
                'age': patient.age,
                'snils': patient.snils or '-',
                'enp': patient.enp or '-',
                'benefit_category': patient.benefit_category.name if patient.benefit_category else '-',
                'diagnosis_code': patient.diagnosis_code or '-',
                'diagnosis_name': patient.diagnosis_name or '-',
                'phone': patient.phone or '-',
                'address': patient.address or '-',
                'is_active': patient.is_active,
                'total_drugs': drug_supplies.count(),
                'active_drugs': active_drugs,
                'urgent_drugs': urgent_drugs,
                'expired_drugs': expired_drugs,
            })
        
        response_data = {
            'success': True,
            'patients': patients_data,
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': patients_page.has_next(),
                'has_previous': patients_page.has_previous(),
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def patient_detail_api(request, patient_id):
    """API для получения детальной информации о пациенте"""
    try:
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Получаем все препараты пациента
        drug_supplies = patient.drug_supplies.select_related('drug').all()
        
        supplies_data = []
        for supply in drug_supplies:
            supplies_data.append({
                'id': supply.id,
                'drug_name': supply.drug.name,
                'drug_inn': supply.drug.inn or '-',
                'monthly_need': supply.monthly_need,
                'dose_regimen': supply.dose_regimen or '-',
                'prescribed': supply.prescribed or '-',
                'prescription_date': supply.prescription_date.strftime('%d.%m.%Y') if supply.prescription_date else '-',
                'issue_date': supply.issue_date.strftime('%d.%m.%Y') if supply.issue_date else '-',
                'supplied_until': supply.supplied_until.strftime('%d.%m.%Y') if supply.supplied_until else '-',
                'days_remaining': supply.days_remaining,
                'is_urgent': supply.is_urgent,
                'is_expired': supply.is_expired,
                'status': supply.status,
                'status_display': supply.get_status_display(),
                'doctor_name': supply.doctor_name or '-',
                'recipe_number': supply.recipe_number or '-',
                'note': supply.note or '',
            })
        
        patient_data = {
            'id': patient.id,
            'full_name': patient.full_name,
            'birth_date': patient.birth_date.strftime('%d.%m.%Y'),
            'age': patient.age,
            'snils': patient.snils or '-',
            'enp': patient.enp or '-',
            'benefit_category': patient.benefit_category.name if patient.benefit_category else '-',
            'benefit_category_id': patient.benefit_category.id if patient.benefit_category else None,
            'diagnosis_code': patient.diagnosis_code or '-',
            'diagnosis_name': patient.diagnosis_name or '-',
            'address': patient.address or '-',
            'phone': patient.phone or '-',
            'is_active': patient.is_active,
            'drug_supplies': supplies_data,
        }
        
        return JsonResponse({
            'success': True,
            'patient': patient_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def categories_api(request):
    """API для получения списка категорий льгот"""
    try:
        categories = BenefitCategory.objects.filter(is_active=True).annotate(
            patients_count=Count('patients')
        ).order_by('name')
        
        categories_data = []
        for category in categories:
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'code': category.code or '-',
                'is_for_children': category.is_for_children,
                'default_coverage_percentage': category.default_coverage_percentage,
                'financing_source': category.financing_source or '-',
                'patients_count': category.patients_count,
            })
        
        return JsonResponse({
            'success': True,
            'categories': categories_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def statistics_api(request):
    """API для получения статистики по льготникам"""
    try:
        # Общая статистика
        total_patients = Patient.objects.filter(is_active=True).count()
        total_categories = BenefitCategory.objects.filter(is_active=True).count()
        
        # Статистика по категориям
        categories_stats = BenefitCategory.objects.filter(is_active=True).annotate(
            patients_count=Count('patients', filter=Q(patients__is_active=True))
        ).values('id', 'name', 'patients_count')
        
        # Статистика по препаратам
        today = timezone.now().date()
        urgent_supplies = PatientDrugSupply.objects.filter(
            supplied_until__lte=today + timedelta(days=7),
            supplied_until__gte=today,
            status__in=['pending', 'active']
        ).count()
        
        expired_supplies = PatientDrugSupply.objects.filter(
            supplied_until__lt=today,
            status__in=['pending', 'active']
        ).count()
        
        return JsonResponse({
            'success': True,
            'statistics': {
                'total_patients': total_patients,
                'total_categories': total_categories,
                'urgent_supplies': urgent_supplies,
                'expired_supplies': expired_supplies,
                'categories_stats': list(categories_stats),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
