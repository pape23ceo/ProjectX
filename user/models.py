import secrets
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='otp_profile')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        # Generates a secure 6-digit random number string
        self.otp = "".join(secrets.choice("0123456789") for _ in range(6))
        self.created_at = timezone.now()
        self.save()
        return self.otp

    def is_valid(self):
        # OTP is valid for 5 minutes
        return timezone.now() < self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.user.username} - {self.otp}"