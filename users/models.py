from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models

from .managers import UserManager
from .utils import AVATAR_DEFAULT_LETTER, generate_avatar


USER_NAME_MAX_LENGTH = 124
USER_SURNAME_MAX_LENGTH = 124
USER_PHONE_MAX_LENGTH = 12
USER_ABOUT_MAX_LENGTH = 256

AVATAR_UPLOAD_DIR = 'avatars/'
AVATAR_FILENAME_TEMPLATE = 'avatar_{username}.png'
EMAIL_LOCAL_PART_INDEX = 0
EMAIL_SEPARATOR = '@'

PROJECT_MODEL_REF = 'projects.Project'


class User(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя."""

    email = models.EmailField(unique=True, verbose_name='Email')
    name = models.CharField(
        max_length=USER_NAME_MAX_LENGTH,
        verbose_name='Имя',
    )
    surname = models.CharField(
        max_length=USER_SURNAME_MAX_LENGTH,
        verbose_name='Фамилия',
    )
    avatar = models.ImageField(
        upload_to=AVATAR_UPLOAD_DIR,
        verbose_name='Аватар',
        blank=True,
    )
    phone = models.CharField(
        max_length=USER_PHONE_MAX_LENGTH,
        verbose_name='Телефон',
        blank=True,
        default='',
    )
    github_url = models.URLField(blank=True, verbose_name='GitHub')
    about = models.TextField(
        max_length=USER_ABOUT_MAX_LENGTH,
        blank=True,
        verbose_name='О себе',
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    favorites = models.ManyToManyField(
        PROJECT_MODEL_REF,
        blank=True,
        related_name='interested_users',
        verbose_name='Избранные проекты',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'surname']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.surname} {self.name}'

    def save(self, *args, **kwargs):
        """Генерируем аватарку при создании нового пользователя."""
        if not self.pk and not self.avatar:
            letter = self.name[0] if self.name else AVATAR_DEFAULT_LETTER
            avatar_io = generate_avatar(letter)
            username = self.email.split(EMAIL_SEPARATOR)[
                EMAIL_LOCAL_PART_INDEX]
            filename = AVATAR_FILENAME_TEMPLATE.format(username=username)
            self.avatar.save(
                filename,
                ContentFile(avatar_io.read()),
                save=False,
            )
        super().save(*args, **kwargs)
