import secrets
from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User
import random
import datetime
# from django.conf import settings

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # email = models.EmailField(max_length=255, unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def generate_otp(cls, user):
        code = str(random.randint(100000, 999999))
        otp, created = cls.objects.update_or_create(
            user=user,
            defaults={'otp': code, 'created_at': datetime.datetime.now()}
        )
        return code