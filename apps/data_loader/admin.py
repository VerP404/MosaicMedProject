from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import FileUploadForm
from .handlers.oms_data import handle_oms_data
from .models.oms_data import OMSData


class OMSDataAdmin(admin.ModelAdmin):
    change_list_template = 'admin/omsdata/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload/', self.upload_file, name='upload_omsdata'),
        ]
        return custom_urls + urls

    def upload_file(self, request):
        if request.method == 'POST':
            form = FileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                try:
                    handle_oms_data(file, request)  # Используем вашу функцию для обработки файла
                    messages.success(request, "Файл успешно загружен и обработан.")
                except Exception as e:
                    messages.error(request, f"Ошибка: {str(e)}")
                return redirect('..')
        else:
            form = FileUploadForm()
        return render(request, 'admin/omsdata/upload.html', {'form': form})


admin.site.register(OMSData, OMSDataAdmin)
