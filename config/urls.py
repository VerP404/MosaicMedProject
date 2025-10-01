# urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.home.views import custom_404, custom_500, custom_403

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.home.urls')),
    path('data_loader/', include('apps.data_loader.urls', namespace='data_loader')),
    path('organization/', include('apps.organization.urls')),
    path('personnel/', include('apps.personnel.urls')),
    path('sql_manager/', include('apps.sql_manager.urls')),
    path('peopledash/', include('apps.peopledash.urls')),
    path('plan/', include('apps.plan.urls')),
    path('people/', include('apps.people.urls')),
    path('api/', include('apps.api.urls')),
    path('', include('apps.references.urls')),
]
# Обслуживание медиа файлов
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns

# Обработчики ошибок для продакшена
handler404 = custom_404
handler500 = custom_500
handler403 = custom_403
