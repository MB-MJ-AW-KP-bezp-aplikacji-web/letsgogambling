from django.apps import AppConfig
import logging

logger = logging.getLogger('auditlog')


class BaseConfig(AppConfig):
    name = 'casino.base'

    def ready(self):
        """Connect signal handlers when app is ready."""
        from auditlog.models import LogEntry
        from django.db.models.signals import post_save

        def log_audit_to_stdout(sender, instance, created, **kwargs):
            """Log audit entries to stdout."""
            if created:
                action = instance.get_action_display()
                actor = instance.actor.username if instance.actor else 'System'
                model_name = instance.content_type.model if instance.content_type else 'Unknown'

                # Format the log message
                msg = f"{action} on {model_name} (ID: {instance.object_id}) by {actor}"

                # Add changes if available
                if instance.changes:
                    changes_str = ', '.join([
                        f"{field}: {old} → {new}"
                        for field, (old, new) in instance.changes_dict.items()
                    ])
                    msg += f" | Changes: {changes_str}"

                logger.info(msg)

        # Connect the signal
        post_save.connect(log_audit_to_stdout, sender=LogEntry)
