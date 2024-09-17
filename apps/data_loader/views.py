from django.views.generic.edit import FormView
from .forms import FileUploadForm
from .handlers import oms_data


class UploadView(FormView):
    template_name = 'admin/omsdata/upload.html'
    form_class = FileUploadForm

    def form_valid(self, form):
        file = form.cleaned_data['file']
        oms_data(file, self.request)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('admin:data_loader_omsdata_changelist')
