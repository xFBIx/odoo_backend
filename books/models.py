from django.db import models
from django.contrib.auth.models import User
import random


def random_ISBN():
    return randaom.randint(1000000000000, 9999999999999)


class Book(models.Model):
    librarain = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    author = models.CharField(max_length=100)
    ISBN = models.CharField(max_length=13, default=random_ISBN)
    published_date = models.DateField()
    added_date = models.DateField(auto_now_add=True)
    is_borrowed = models.BooleanField(default=False)
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.title
