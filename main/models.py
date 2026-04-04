from django.conf import settings
from django.db import models

class UserSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='settings' # You can access settings via user.settings
    )
    # Add your specific settings fields here
    theme = models.CharField(max_length=20, default='light')
    timezone = models.CharField(max_length=50, default='UTC')
    receive_notifications = models.BooleanField(default=True)
    location = models.CharField(max_length=100, default='')
    

    def __str__(self):
        return f"{self.user.username}'s settings"
