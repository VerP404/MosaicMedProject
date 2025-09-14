from .models import MainSettings
from apps.organization.models import MedicalOrganization

def portal_context(request):
    """Context processor для передачи переменных портала во все шаблоны"""
    try:
        main_settings = MainSettings.objects.first()
        organization = MedicalOrganization.objects.first()
        
        if main_settings and request:
            # Формируем динамические URL на основе текущего хоста
            scheme = 'https' if request.is_secure() else 'http'
            host = request.get_host()
            host_only = host.split(':')[0]
            
            dash_url = f"{scheme}://{host_only}:{main_settings.dash_port}"
            dash_chief_url = f"{scheme}://{host_only}:{main_settings.dash_chief_port}"
            
            return {
                'main_settings': main_settings,
                'organization': organization,
                'dash_url': dash_url,
                'dash_chief_url': dash_chief_url,
            }
    except:
        pass
    
    return {
        'main_settings': None,
        'organization': None,
        'dash_url': '#',
        'dash_chief_url': '#',
    }
