from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    """
    自定义用户管理器，用于创建用户和超级用户。
    """
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_superuser', True) # Added for clarity

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    自定义用户模型，继承AbstractBaseUser和PermissionsMixin。
    使用username作为USERNAME_FIELD，并包含is_active, is_staff, date_joined等默认字段。
    """
    username = models.CharField(unique=True, max_length=150, verbose_name='用户名')
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    is_staff = models.BooleanField(default=False, verbose_name='是否为员工')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='加入日期')

    objects = CustomUserManager()

    USERNAME_FIELD = 'username' # 定义用于认证的字段
    REQUIRED_FIELDS = [] # 对于最小化用户模型，不强制要求额外字段

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.username