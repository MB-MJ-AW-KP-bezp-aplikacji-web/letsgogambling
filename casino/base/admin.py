from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from auditlog.models import LogEntry
from .models import Codes, UsedCodes, History


@admin.register(Codes)
class CodesAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'value']
    search_fields = ['name']
    list_filter = ['value']

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Add audit log history to the change form."""
        extra_context = extra_context or {}
        if object_id:
            content_type = ContentType.objects.get_for_model(Codes)
            extra_context['audit_logs'] = LogEntry.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).order_by('-timestamp')[:20]
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(UsedCodes)
class UsedCodesAdmin(admin.ModelAdmin):
    list_display = ['id', 'u_id', 'c_id']
    list_filter = ['u_id']
    search_fields = ['c_id__username']
    raw_id_fields = ['u_id', 'c_id']

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Add audit log history to the change form."""
        extra_context = extra_context or {}
        if object_id:
            content_type = ContentType.objects.get_for_model(UsedCodes)
            extra_context['audit_logs'] = LogEntry.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).order_by('-timestamp')[:20]
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'u_id', 'amount', 'cashout_time']
    list_filter = ['cashout_time']
    search_fields = ['u_id__username']
    date_hierarchy = 'cashout_time'
    raw_id_fields = ['u_id']

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Add audit log history to the change form."""
        extra_context = extra_context or {}
        if object_id:
            content_type = ContentType.objects.get_for_model(History)
            extra_context['audit_logs'] = LogEntry.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).order_by('-timestamp')[:20]
        return super().changeform_view(request, object_id, form_url, extra_context)
