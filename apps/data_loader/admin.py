from django.contrib import admin
from django.shortcuts import render, redirect
from django.contrib import messages
from .handlers.oms_data import handle_oms_data
from .models.oms_data import OMSData


class OMSDataAdmin(admin.ModelAdmin):
    change_list_template = 'admin/omsdata/change_list.html'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('upload/', self.upload_file, name='upload_omsdata'),
        ]
        return custom_urls + urls

    def upload_file(self, request):
        if request.method == 'POST':
            file = request.FILES.get('file')
            if file:
                handle_oms_data(file, request)
                messages.success(request, "Файл успешно загружен.")
                return redirect('..')
            messages.error(request, "Не выбран файл.")
        return render(request, 'admin/omsdata/upload.html')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset


admin.site.register(OMSData, OMSDataAdmin)
