from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    auth_user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name or self.auth_user.username
