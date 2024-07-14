from django.db import models
from django.contrib.auth.models import User

USER_ROLE_CHOICES = [
    ("Customer", "Customer"),
    ("Librarian", "Librarian"),
    ("Admin", "Admin"),
]


class UserProfile(models.Model):
    auth_user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    role = models.CharField(
        max_length=100, choices=USER_ROLE_CHOICES, default="Customer"
    )

    def __str__(self):
        return self.name or self.auth_user.username
