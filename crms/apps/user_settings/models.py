from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dark_mode = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    default_credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=3000)
    overdue_grace_days = models.PositiveSmallIntegerField(default=7)
    reminder_threshold_days = models.PositiveSmallIntegerField(default=3)
    expiry_window_days = models.PositiveSmallIntegerField(default=7)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    block_over_limit = models.BooleanField(default=True)

    def __str__(self):
        return f"Settings for {self.user.username}"


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSettings.objects.get_or_create(user=instance)

