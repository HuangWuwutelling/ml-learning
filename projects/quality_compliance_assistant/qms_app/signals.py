import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from .models import Manufacturer, Product, DefectType, Recall, Capa, Complaint, AuditLog

REGISTERED = [Manufacturer, Product, DefectType, Recall, Capa, Complaint]

def _snapshot(instance):
    # model_to_dict yields date/datetime/Decimal, which AuditLog's plain
    # JSONField encoder rejects; round-trip through DjangoJSONEncoder to
    # normalise them to strings before they reach the DB.
    try:
        return json.loads(json.dumps(model_to_dict(instance), cls=DjangoJSONEncoder))
    except Exception:
        return {'id': instance.pk}

@receiver(pre_save)
def capture_before(sender, instance, **kwargs):
    if sender not in REGISTERED:
        return
    if instance.pk:
        try:
            instance._before = _snapshot(sender.objects.get(pk=instance.pk))
        except sender.DoesNotExist:
            instance._before = None
    else:
        instance._before = None

@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    if sender not in REGISTERED:
        return
    AuditLog.objects.create(
        action='create' if created else 'update',
        target_model=sender.__name__,
        target_id=instance.pk,
        before_json=getattr(instance, '_before', None),
        after_json=_snapshot(instance),
    )
    # Clean up the per-instance snapshot attribute set by capture_before so it
    # does not leak across requests/save cycles (e.g. into __dict__/__slots__).
    try:
        del instance._before
    except AttributeError:
        pass

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender not in REGISTERED:
        return
    AuditLog.objects.create(
        action='delete',
        target_model=sender.__name__,
        target_id=instance.pk,
        before_json=_snapshot(instance),
        after_json=None,
    )
