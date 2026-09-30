from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from .crypto import decrypt, encrypt


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name='E-mail')
    first_name = models.CharField(max_length=100, verbose_name='Nome')
    last_name = models.CharField(max_length=100, blank=True, verbose_name='Sobrenome')
    photo = models.ImageField(
        upload_to='photos/',
        null=True, blank=True,
        verbose_name='Foto do perfil'
    )
    openai_api_key_encrypted = models.TextField(
        blank=True, default='',
        verbose_name='Chave da API OpenAI (criptografada)'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        return self.first_name

    @property
    def openai_api_key(self):
        return decrypt(self.openai_api_key_encrypted)

    @openai_api_key.setter
    def openai_api_key(self, value):
        self.openai_api_key_encrypted = encrypt((value or '').strip())

    @property
    def has_openai_key(self):
        return bool(self.openai_api_key)

    @property
    def openai_api_key_masked(self):
        key = self.openai_api_key
        if not key:
            return ''
        return f'{key[:7]}…{key[-4:]}'
