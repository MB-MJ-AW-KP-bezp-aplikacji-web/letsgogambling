from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from auditlog.models import LogEntry
from .models import GameRound, Bet


@admin.register(GameRound)
class GameRoundAdmin(admin.ModelAdmin):
    list_display = ['round_number', 'status', 'winning_color', 'winning_slot', 'created_at']
    list_filter = ['status', 'winning_color', 'created_at']
    search_fields = ['round_number']
    readonly_fields = ['created_at', 'spin_time']
    date_hierarchy = 'created_at'

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Add audit log history to the change form."""
        extra_context = extra_context or {}
        if object_id:
            content_type = ContentType.objects.get_for_model(GameRound)
            extra_context['audit_logs'] = LogEntry.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).order_by('-timestamp')[:20]
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'round', 'color', 'amount', 'payout', 'placed_at']
    list_filter = ['color', 'placed_at']
    search_fields = ['user__username', 'round__round_number']
    readonly_fields = ['placed_at']
    raw_id_fields = ['user', 'round']
    date_hierarchy = 'placed_at'

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Add audit log history to the change form."""
        extra_context = extra_context or {}
        if object_id:
            content_type = ContentType.objects.get_for_model(Bet)
            extra_context['audit_logs'] = LogEntry.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).order_by('-timestamp')[:20]
        return super().changeform_view(request, object_id, form_url, extra_context)
