from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import User
from .forms import RegisterForm, LoginForm, EditProfileForm, CustomPasswordChangeForm


def register_view(request):
    """Регистрация нового пользователя."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data['email'],
                name=form.cleaned_data['name'],
                surname=form.cleaned_data['surname'],
                password=form.cleaned_data['password'],
            )
            login(request, user)
            return redirect('/projects/list/')
        return render(request, 'users/register.html', {'form': form})

    form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


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
                return redirect('/projects/list/')
            else:
                form.add_error(None, 'Неверный имейл или пароль')
        return render(request, 'users/login.html', {'form': form})

    form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """Выход."""
    logout(request)
    return redirect('/projects/list/')


def user_detail_view(request, user_id):
    """Профиль пользователя."""
    profile_user = get_object_or_404(User, pk=user_id)
    return render(request, 'users/user-details.html', {'user': profile_user})


def participants_view(request):
    """Список пользователей с фильтрацией (Вариант 1)."""
    users_qs = User.objects.all().order_by('id')
    active_filter = None

    filter_param = request.GET.get('filter')
    if request.user.is_authenticated and filter_param:
        active_filter = filter_param

        if filter_param == 'owners-of-favorite-projects':
            # Авторы избранных проектов
            favorite_projects = request.user.favorites.all()
            users_qs = User.objects.filter(
                owned_projects__in=favorite_projects
            ).distinct().order_by('id')

        elif filter_param == 'owners-of-participating-projects':
            # Авторы проектов, в которых я участвую
            participated_projects = request.user.participated_projects.all()
            users_qs = User.objects.filter(
                owned_projects__in=participated_projects
            ).distinct().order_by('id')

        elif filter_param == 'interested-in-my-projects':
            # Пользователи, которым нравятся мои проекты
            my_projects = request.user.owned_projects.all()
            users_qs = User.objects.filter(
                favorites__in=my_projects
            ).distinct().order_by('id')

        elif filter_param == 'participants-of-my-projects':
            # Участники моих проектов
            my_projects = request.user.owned_projects.all()
            users_qs = User.objects.filter(
                participated_projects__in=my_projects
            ).exclude(pk=request.user.pk).distinct().order_by('id')

    paginator = Paginator(users_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'users/participants.html', {
        'participants': page_obj,
        'page_obj': page_obj,
        'active_filter': active_filter,
    })


@login_required
def edit_profile_view(request):
    """Редактирование профиля."""
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(f'/users/{request.user.pk}/')
        return render(request, 'users/edit_profile.html', {'form': form})

    form = EditProfileForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})


@login_required
def change_password_view(request):
    """Смена пароля."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect(f'/users/{request.user.pk}/')
        return render(request, 'users/change_password.html', {'form': form})

    form = CustomPasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})