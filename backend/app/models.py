from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, group="Student" , **extra_fields):
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        group = Group.objects.get(name=group)
        user.groups.add(group) 
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, group="Admin",**extra_fields)

class CustomUser(AbstractUser):
    email = models.EmailField(_("email address"), unique=True)
    user_id = models.CharField(max_length=6, unique=True, default=0)
    date_joined = models.DateTimeField(default=timezone.now)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    # Specify related_name for groups field
    groups = models.ManyToManyField(
        Group,
        related_name='custom_users',
        related_query_name='custom_user',
        blank=True,
        verbose_name=_('groups'),
        help_text=_('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
    )

    # Specify related_name for user_permissions field
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_users',
        related_query_name='custom_user',
        blank=True,
        verbose_name=_('user permissions'),
        help_text=_('Specific permissions for this user.'),
    )
