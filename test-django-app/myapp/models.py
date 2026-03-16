# intentional bugs for django-minion to find and fix
import os,sys  # E401: multiple imports on one line
from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10,decimal_places=2)  # E231: missing whitespace after ','

    def __str__(self):
        return f"{self.name} - ${self.price}"

    # BUG: discounted_price method is missing — tests will fail without it
