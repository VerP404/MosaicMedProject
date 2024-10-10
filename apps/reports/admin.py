from django.contrib import admin

from apps.reports.models import DeleteEmd, InvalidationReason


@admin.register(DeleteEmd)
class DeleteEmdAdmin(admin.ModelAdmin):
    list_display = ('oid_medical_organization', 'oid_document', 'goal', 'added_date')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # при редактировании объекта
            return self.readonly_fields + ('oid_medical_organization',)
        return self.readonly_fields


@admin.register(InvalidationReason)
class InvalidationReasonAdmin(admin.ModelAdmin):
    list_display = ('reason_text',)
