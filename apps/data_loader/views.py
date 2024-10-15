from django.shortcuts import render, get_object_or_404, redirect
from .forms import FileUploadForm
from .models.oms_data import DataType, DataImport


def upload_file(request, data_type_id):
    data_type = get_object_or_404(DataType, id=data_type_id)
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form_object = form.save(commit=False)
            form_object.data_type = data_type
            form_object.save()
            # Call the DataLoader here
            # loader = DataLoader(engine=engine, ...)
            # loader.load_data(form_object.csv_file.path)
            return redirect('data_upload_dashboard')
    else:
        form = FileUploadForm()

    return render(request, 'upload_file.html', {'form': form, 'data_type': data_type})


def data_upload_dashboard(request):
    data_types = DataType.objects.all()
    for data_type in data_types:
        last_import = DataImport.objects.filter(data_type=data_type).order_by('-date_added').first()
        data_type.last_import_date = last_import.date_added if last_import else None

    return render(request, 'data_upload_dashboard.html', {'data_types': data_types})
