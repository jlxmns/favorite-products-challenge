from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        from api.models import AuthToken

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        user = self.create_user(email, name, password, **extra_fields)
        AuthToken.objects.create(user=user)

        return user


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        CUSTOMER = "CUSTOMER", "Cliente"

    username = None
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=255, choices=Role.choices, default=Role.CUSTOMER
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    @property
    def token(self):
        obj_token = self.tokens.first()
        if obj_token:
            return obj_token.key
        return None


class AuditedModel(models.Model):
    date_created = models.DateTimeField("Criado em", auto_now_add=True)
    date_changed = models.DateTimeField("Modificado em", auto_now=True)
    active = models.BooleanField(verbose_name="Ativo", default=True)

    class Meta:
        abstract = True


class Product(AuditedModel):
    api_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    description = models.TextField()
    category = models.CharField(max_length=255)
    image = models.URLField()
    rating_rate = models.DecimalField(decimal_places=1, max_digits=3, null=True, blank=True)
    rating_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title


class FavoriteProducts(AuditedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "product")
