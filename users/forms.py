import re
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import User


class RegisterForm(forms.Form):
    """Форма регистрации."""
    name = forms.CharField(max_length=124, label='Имя')
    surname = forms.CharField(max_length=124, label='Фамилия')
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email


class LoginForm(forms.Form):
    """Форма входа."""
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


def normalize_phone(phone):
    if phone.startswith('8') and len(phone) == 11:
        return '+7' + phone[1:]
    return phone


class EditProfileForm(forms.ModelForm):
    """Форма редактирования профиля."""

    class Meta:
        model = User
        fields = ['name', 'surname', 'avatar', 'about', 'phone', 'github_url']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            return phone

        if not (re.match(r'^8\d{10}$', phone) or re.match(r'^\+7\d{10}$', phone)):
            raise forms.ValidationError(
                'Введите номер в формате 8XXXXXXXXXX или +7XXXXXXXXXX'
            )

        normalized = normalize_phone(phone)

        qs = User.objects.filter(phone__in=[normalized, phone])
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Этот номер телефона уже занят.')

        return normalized

    def clean_github_url(self):
        url = self.cleaned_data.get('github_url', '').strip()
        if not url:
            return url
        if not url.startswith(('http://github.com', 'https://github.com',
                                'http://www.github.com', 'https://www.github.com')):
            raise forms.ValidationError('Ссылка должна вести на GitHub.')
        return url


class CustomPasswordChangeForm(PasswordChangeForm):
    """Форма смены пароля."""
    pass