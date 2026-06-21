import re

from django import forms

from .models import (
    USER_NAME_MAX_LENGTH,
    USER_SURNAME_MAX_LENGTH,
    User,
)
from .utils import normalize_phone


PHONE_PATTERN_8 = r'^8\d{10}$'
PHONE_PATTERN_PLUS7 = r'^\+7\d{10}$'
PHONE_FORMAT_ERROR = (
    'Введите номер в формате 8XXXXXXXXXX или +7XXXXXXXXXX'
)
PHONE_DUPLICATE_ERROR = 'Этот номер телефона уже занят.'

GITHUB_URL_PREFIXES = (
    'http://github.com',
    'https://github.com',
    'http://www.github.com',
    'https://www.github.com',
)
GITHUB_URL_ERROR = 'Ссылка должна вести на GitHub.'

EMAIL_DUPLICATE_ERROR = 'Пользователь с таким email уже существует.'

LABEL_NAME = 'Имя'
LABEL_SURNAME = 'Фамилия'
LABEL_EMAIL = 'Email'
LABEL_PASSWORD = 'Пароль'


class RegisterForm(forms.Form):
    """Форма регистрации."""

    name = forms.CharField(
        max_length=USER_NAME_MAX_LENGTH,
        label=LABEL_NAME,
    )
    surname = forms.CharField(
        max_length=USER_SURNAME_MAX_LENGTH,
        label=LABEL_SURNAME,
    )
    email = forms.EmailField(label=LABEL_EMAIL)
    password = forms.CharField(
        label=LABEL_PASSWORD,
        widget=forms.PasswordInput,
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(EMAIL_DUPLICATE_ERROR)
        return email

    def save(self):
        """Создаёт нового пользователя на основе данных формы."""
        return User.objects.create_user(
            email=self.cleaned_data['email'],
            name=self.cleaned_data['name'],
            surname=self.cleaned_data['surname'],
            password=self.cleaned_data['password'],
        )


class LoginForm(forms.Form):
    """Форма входа."""

    email = forms.EmailField(label=LABEL_EMAIL)
    password = forms.CharField(
        label=LABEL_PASSWORD,
        widget=forms.PasswordInput,
    )


class EditProfileForm(forms.ModelForm):
    """Форма редактирования профиля."""

    class Meta:
        model = User
        fields = ['name', 'surname', 'avatar', 'about', 'phone', 'github_url']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            return phone

        if not (
            re.match(PHONE_PATTERN_8, phone)
            or re.match(PHONE_PATTERN_PLUS7, phone)
        ):
            raise forms.ValidationError(PHONE_FORMAT_ERROR)

        normalized = normalize_phone(phone)

        qs = User.objects.filter(phone__in=[normalized, phone])
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(PHONE_DUPLICATE_ERROR)

        return normalized

    def clean_github_url(self):
        url = self.cleaned_data.get('github_url', '').strip()
        if not url:
            return url
        if not url.startswith(GITHUB_URL_PREFIXES):
            raise forms.ValidationError(GITHUB_URL_ERROR)
        return url
