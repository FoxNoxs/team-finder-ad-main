import io
import random
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile


class UserManager(BaseUserManager):
    """Менеджер для создания пользователей."""

    def create_user(self, email, name, surname, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, surname=surname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, surname, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, surname, password, **extra_fields)


def generate_avatar(letter):
    """Генерирует аватарку с первой буквой имени."""
    colors = [
        (100, 149, 237),
        (144, 238, 144),
        (255, 182, 193),
        (255, 165, 79),
        (147, 112, 219),
        (64, 224, 208),
        (135, 206, 235),
    ]
    bg_color = random.choice(colors)
    size = 200

    img = Image.new('RGB', (size, size), color=bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype('static/fonts/Raleway-Regular.ttf', size=100)
    except Exception:
        font = ImageFont.load_default(size=100)

    letter = letter.upper()
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) / 2 - bbox[0]
    y = (size - text_height) / 2 - bbox[1]
    draw.text((x, y), letter, fill=(255, 255, 255), font=font)

    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    return output


class User(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя."""

    email = models.EmailField(unique=True, verbose_name='Email')
    name = models.CharField(max_length=124, verbose_name='Имя')
    surname = models.CharField(max_length=124, verbose_name='Фамилия')
    avatar = models.ImageField(
        upload_to='avatars/',
        verbose_name='Аватар',
        blank=True,
    )
    phone = models.CharField(
        max_length=12,
        verbose_name='Телефон',
        blank=True,
        default='',
    )
    github_url = models.URLField(blank=True, verbose_name='GitHub')
    about = models.TextField(max_length=256, blank=True, verbose_name='О себе')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Вариант 1 — избранные проекты
    favorites = models.ManyToManyField(
        'projects.Project',
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
            letter = self.name[0] if self.name else 'U'
            avatar_io = generate_avatar(letter)
            filename = f'avatar_{self.email.split("@")[0]}.png'
            self.avatar.save(
                filename,
                ContentFile(avatar_io.read()),
                save=False,
            )
        super().save(*args, **kwargs)