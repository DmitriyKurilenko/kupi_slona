"""
Signals for automatic cleanup of elephant images
"""
import os
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from .models import Elephant


@receiver(pre_delete, sender=Elephant)
def delete_elephant_image(sender, instance, **kwargs):
    """
    Delete elephant image file when elephant instance is deleted
    """
    if instance.image:
        # Check if file exists before trying to delete
        if os.path.isfile(instance.image.path):
            try:
                os.remove(instance.image.path)
            except OSError:
                # File might have been already deleted or permission issue
                pass


@receiver(pre_save, sender=Elephant)
def delete_old_elephant_image_on_update(sender, instance, **kwargs):
    """
    Delete old image file when elephant image is updated
    """
    if not instance.pk:
        # New instance, nothing to delete
        return

    try:
        old_instance = Elephant.objects.get(pk=instance.pk)
    except Elephant.DoesNotExist:
        # Instance doesn't exist yet
        return

    # If image has changed, delete the old one
    if old_instance.image and old_instance.image != instance.image:
        if os.path.isfile(old_instance.image.path):
            try:
                os.remove(old_instance.image.path)
            except OSError:
                pass
