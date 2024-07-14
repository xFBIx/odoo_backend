from django.db import models
from django.contrib.auth.models import User
import random
from users.models import UserProfile


def random_ISBN():
    return random.randint(1000000000000, 9999999999999)


GENRE_TYPE_CHOICES = [
    ("Science Fiction", "Science Fiction"),
    ("Mystery", "Mystery"),
    ("Thriller", "Thriller"),
    ("Romance", "Romance"),
    ("Horror", "Horror"),
    ("Comic", "Comic"),
]


# class Book(models.Model):
#     librarain = models.ForeignKey(User, on_delete=models.CASCADE)
#     title = models.CharField(max_length=100)
#     description = models.TextField()
#     author = models.CharField(max_length=100)
#     ISBN = models.CharField(max_length=13, default=random_ISBN, unique=True)
#     year = models.IntegerField()
#     genre = models.CharField(max_length=100, choices=GENRE_TYPE_CHOICES)
#     published_date = models.DateField()
#     added_date = models.DateField(auto_now_add=True)
#     quantity = models.IntegerField(default=1)
#     available = models.IntegerField(default=1)

#     def __str__(self):
#         return self.title or self.ISBN


class Book(models.Model):
    isbn_10 = models.CharField(max_length=10, blank=True, null=True)
    isbn_13 = models.CharField(max_length=13, unique=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    authors = models.CharField(max_length=200, null=True)
    publisher = models.CharField(max_length=100)
    published_date = models.CharField(max_length=20, null=True)
    description = models.TextField(blank=True, null=True)
    page_count = models.IntegerField(blank=True, null=True)
    categories = models.CharField(max_length=200, blank=True, null=True)
    language = models.CharField(max_length=10, blank=True, null=True)
    preview_link = models.URLField(max_length=500, blank=True, null=True)
    info_link = models.URLField(max_length=500, blank=True, null=True)
    small_thumbnail = models.URLField(max_length=500, blank=True, null=True)
    thumbnail = models.URLField(max_length=500, blank=True, null=True)
    quantity = models.IntegerField(default=1)
    available = models.IntegerField(default=1)

    def __str__(self):
        return self.title


class Borrowing(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    late_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.name} - {self.book.title}"


class Notification(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.name} - {self.message[:20]}"
