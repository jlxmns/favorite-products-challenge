import os

from django.db import models
import binascii

from FavoriteProductsAPI import settings
from core.models import AuditedModel


class AuthToken(AuditedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tokens')
    key = models.CharField(max_length=40, unique=True, db_index=True)

    def __str__(self):
        return f"Token (user={self.user.email}, key={self.key})"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_key():
        return binascii.hexlify(os.urandom(20)).decode()
