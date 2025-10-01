from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def portal_context(request):
    """Контекстный процессор для портала"""
    return {
        'site_name': 'МозаикаМед',
        'organization': getattr(settings, 'ORGANIZATIONS', 'МозаикаМед'),
    }

def home(request):
    """Главная страница"""
    return render(request, 'home/home.html')

def check_system_status(request):
    """Проверка статуса системы"""
    import psutil
    import time
    from django.http import JsonResponse
    
    try:
        # Получаем информацию о системе
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status = {
            'timestamp': time.time(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_percent': disk.percent,
            'disk_free_gb': round(disk.free / (1024**3), 2),
            'status': 'ok'
        }
        
        return JsonResponse(status)
        
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса системы: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def custom_404(request, exception=None):
    """Кастомная страница 404"""
    logger.warning(f"404 ошибка: {request.path} - {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    
    context = {
        'request_path': request.path,
        'site_name': 'МозаикаМед',
        'organization': getattr(settings, 'ORGANIZATIONS', 'МозаикаМед'),
    }
    
    return render(request, '404.html', context, status=404)

def custom_500(request):
    """Кастомная страница 500"""
    logger.error(f"500 ошибка: {request.path} - {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    
    context = {
        'request_path': request.path,
        'site_name': 'МозаикаМед',
        'organization': getattr(settings, 'ORGANIZATIONS', 'МозаикаМед'),
    }
    
    return render(request, '500.html', context, status=500)

def custom_403(request, exception=None):
    """Кастомная страница 403"""
    logger.warning(f"403 ошибка: {request.path} - {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    
    context = {
        'request_path': request.path,
        'site_name': 'МозаикаМед',
        'organization': getattr(settings, 'ORGANIZATIONS', 'МозаикаМед'),
    }
    
    return render(request, '403.html', context, status=403)

@method_decorator(csrf_exempt, name='dispatch')
class ErrorView(TemplateView):
    """Базовый класс для обработки ошибок"""
    template_name = '404.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'site_name': 'МозаикаМед',
            'organization': getattr(settings, 'ORGANIZATIONS', 'МозаикаМед'),
            'request_path': self.request.path,
        })
        return context