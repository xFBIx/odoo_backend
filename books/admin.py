from django.contrib import admin
from .models import *

admin.site.register(Book)
admin.site.register(Borrowing)
admin.site.register(Notification)
