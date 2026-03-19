from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.core.validators import MinValueValidator
# Create your models here.


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)])
    rating = models.FloatField(default=0.0, help_text="Average user rating")
    
    def __str__(self):
        return f"{self.username} ({self.email})"

