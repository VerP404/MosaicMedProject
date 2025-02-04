from django.shortcuts import render, redirect
from django.core.management import call_command
from django.http import JsonResponse
from .models import ISZLReportSummary


def people_report_view(request):
    reports = ISZLReportSummary.objects.order_by('date_report')
    context = {
        'reports': reports,
    }
    return render(request, 'people/people_report.html', context)


def people_report_view(request):
    reports = ISZLReportSummary.objects.order_by('date_report')
    return render(request, 'people/people_report.html', {'reports': reports})


def generate_iszl_report(request):
    if request.method == 'POST':
        try:
            call_command('create_iszl_reports')
            return JsonResponse({'success': True, 'message': 'Отчет успешно создан.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ошибка при создании отчета: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Неверный метод запроса.'})
