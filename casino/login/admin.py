from django.contrib import admin
from auditlog.admin import LogEntryAdmin
from auditlog.models import LogEntry
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'balance', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
    search_fields = ['username']
    readonly_fields = ['last_login']

    def get_queryset(self, request):
        """Optimize queries."""
        qs = super().get_queryset(request)
        return qs

    def history_view(self, request, object_id, extra_context=None):
        """Custom history view showing audit logs."""
        return self.render_change_form(request, extra_context or {}, obj=self.get_object(request, object_id))

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Add audit log history to the change form."""
        from django.contrib.contenttypes.models import ContentType

        extra_context = extra_context or {}
        if object_id:
            # Get audit logs for this specific object using ContentType
            content_type = ContentType.objects.get_for_model(User)
            extra_context['audit_logs'] = LogEntry.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).order_by('-timestamp')[:20]
        return super().changeform_view(request, object_id, form_url, extra_context)


# Unregister the default LogEntry admin and register our custom one
admin.site.unregister(LogEntry)

@admin.register(LogEntry)
class CustomLogEntryAdmin(LogEntryAdmin):
    list_display = ['created', 'resource_url', 'action', 'actor', 'msg_short', 'reason_display']
    list_filter = ['action', 'timestamp', 'content_type']
    search_fields = ['object_repr', 'changes', 'actor__username', 'additional_data']
    date_hierarchy = 'timestamp'

    def msg_short(self, obj):
        """Show a short version of the changes with reason if available."""
        parts = []

        if obj.changes:
            changes = ', '.join([f"{k}: {v[0]}→{v[1]}" for k, v in list(obj.changes_dict.items())[:3]])
            if len(obj.changes_dict) > 3:
                changes += '...'
            parts.append(changes)

        # Add reason if this is a balance change
        if obj.additional_data and 'balance_change_reason' in obj.additional_data:
            reason = obj.additional_data['balance_change_reason']
            parts.append(f"[Reason: {reason}]")

        return ' | '.join(parts) if parts else '-'
    msg_short.short_description = 'Changes'

    def reason_display(self, obj):
        """Display the balance change reason."""
        if obj.additional_data and 'balance_change_reason' in obj.additional_data:
            return obj.additional_data['balance_change_reason']
        return '-'
    reason_display.short_description = 'Reason'
