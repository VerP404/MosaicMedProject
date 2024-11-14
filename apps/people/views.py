from django.shortcuts import render
from .models import ISZLReportSummary


def people_report_view(request):
    reports = ISZLReportSummary.objects.order_by('date_report')
    context = {
        'reports': reports,
    }
    return render(request, 'people/people_report.html', context)
