from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render

from projects.views import get_paginated_page

from .forms import EditProfileForm, LoginForm, RegisterForm
from .models import User


# --- Шаблоны ---
REGISTER_TEMPLATE = 'users/register.html'
LOGIN_TEMPLATE = 'users/login.html'
PARTICIPANTS_TEMPLATE = 'users/participants.html'
USER_DETAIL_TEMPLATE = 'users/user-details.html'
EDIT_PROFILE_TEMPLATE = 'users/edit_profile.html'
CHANGE_PASSWORD_TEMPLATE = 'users/change_password.html'

# --- Маршруты ---
PROJECT_LIST_ROUTE = 'projects:project_list'
USER_DETAIL_ROUTE = 'users:user_detail'

# --- Ошибки формы ---
LOGIN_ERROR_MESSAGE = 'Неверный имейл или пароль'

# --- Фильтры пользователей ---
FILTER_FAVORITE_OWNERS = 'owners-of-favorite-projects'
FILTER_PARTICIPATING_OWNERS = 'owners-of-participating-projects'
FILTER_INTERESTED_IN_MY = 'interested-in-my-projects'
FILTER_PARTICIPANTS_OF_MY = 'participants-of-my-projects'

ORDER_BY_ID = 'id'


def register_view(request):
    """Регистрация нового пользователя."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(PROJECT_LIST_ROUTE)
        return render(request, REGISTER_TEMPLATE, {'form': form})

    form = RegisterForm()
    return render(request, REGISTER_TEMPLATE, {'form': form})


def login_view(request):
    """Вход в систему."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                return redirect(PROJECT_LIST_ROUTE)
            form.add_error(None, LOGIN_ERROR_MESSAGE)
        return render(request, LOGIN_TEMPLATE, {'form': form})

    form = LoginForm()
    return render(request, LOGIN_TEMPLATE, {'form': form})


def logout_view(request):
    """Выход."""
    logout(request)
    return redirect(PROJECT_LIST_ROUTE)


def user_detail_view(request, user_id):
    """Профиль пользователя."""
    profile_user = get_object_or_404(User, pk=user_id)
    return render(request, USER_DETAIL_TEMPLATE, {'user': profile_user})


def _get_filtered_users(user, filter_param):
    """Возвращает queryset пользователей в зависимости от фильтра."""
    if filter_param == FILTER_FAVORITE_OWNERS:
        favorite_projects = user.favorites.all()
        return User.objects.filter(
            owned_projects__in=favorite_projects,
        ).distinct().order_by(ORDER_BY_ID)

    if filter_param == FILTER_PARTICIPATING_OWNERS:
        participated_projects = user.participated_projects.all()
        return User.objects.filter(
            owned_projects__in=participated_projects,
        ).distinct().order_by(ORDER_BY_ID)

    if filter_param == FILTER_INTERESTED_IN_MY:
        my_projects = user.owned_projects.all()
        return User.objects.filter(
            favorites__in=my_projects,
        ).distinct().order_by(ORDER_BY_ID)

    if filter_param == FILTER_PARTICIPANTS_OF_MY:
        my_projects = user.owned_projects.all()
        return User.objects.filter(
            participated_projects__in=my_projects,
        ).exclude(pk=user.pk).distinct().order_by(ORDER_BY_ID)

    return None


def participants_view(request):
    """Список пользователей с фильтрацией (Вариант 1)."""
    users_qs = User.objects.all().order_by(ORDER_BY_ID)
    active_filter = None

    filter_param = request.GET.get('filter')
    if request.user.is_authenticated and filter_param:
        filtered_qs = _get_filtered_users(request.user, filter_param)
        if filtered_qs is not None:
            users_qs = filtered_qs
            active_filter = filter_param

    page_obj = get_paginated_page(request, users_qs)

    return render(request, PARTICIPANTS_TEMPLATE, {
        'participants': page_obj,
        'page_obj': page_obj,
        'active_filter': active_filter,
    })


@login_required
def edit_profile_view(request):
    """Редактирование профиля."""
    if request.method == 'POST':
        form = EditProfileForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )
        if form.is_valid():
            form.save()
            return redirect(USER_DETAIL_ROUTE, user_id=request.user.pk)
        return render(request, EDIT_PROFILE_TEMPLATE, {'form': form})

    form = EditProfileForm(instance=request.user)
    return render(request, EDIT_PROFILE_TEMPLATE, {'form': form})


@login_required
def change_password_view(request):
    """Смена пароля."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect(USER_DETAIL_ROUTE, user_id=request.user.pk)
        return render(request, CHANGE_PASSWORD_TEMPLATE, {'form': form})

    form = PasswordChangeForm(request.user)
    return render(request, CHANGE_PASSWORD_TEMPLATE, {'form': form})
