from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import (
    PROJECT_STATUS_CLOSED,
    PROJECT_STATUS_OPEN,
    Project,
)


PAGINATION_PAGE_SIZE = 12

PROJECT_LIST_TEMPLATE = 'projects/project_list.html'
PROJECT_DETAIL_TEMPLATE = 'projects/project-details.html'
PROJECT_CREATE_TEMPLATE = 'projects/create-project.html'
FAVORITES_TEMPLATE = 'projects/favorite_projects.html'

PROJECT_DETAIL_ROUTE = 'projects:project_detail'

STATUS_OK = 'ok'
STATUS_ERROR = 'error'
ERROR_PROJECT_NOT_FOUND = 'Project not found'


def get_paginated_page(request, queryset, page_size=PAGINATION_PAGE_SIZE):
    """Возвращает страницу пагинации для queryset."""
    paginator = Paginator(queryset, page_size)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def project_list_view(request):
    """Главная страница — список всех проектов."""
    projects_qs = (
        Project.objects
        .select_related('owner')
        .all()
        .order_by('-created_at')
    )
    page_obj = get_paginated_page(request, projects_qs)
    return render(request, PROJECT_LIST_TEMPLATE, {
        'projects': page_obj,
        'page_obj': page_obj,
    })


def project_detail_view(request, project_id):
    """Страница отдельного проекта."""
    project = get_object_or_404(
        Project.objects.select_related('owner'),
        pk=project_id,
    )
    return render(request, PROJECT_DETAIL_TEMPLATE, {'project': project})


@login_required
def create_project_view(request):
    """Создание нового проекта."""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect(PROJECT_DETAIL_ROUTE, project_id=project.pk)
        return render(request, PROJECT_CREATE_TEMPLATE, {
            'form': form,
            'is_edit': False,
        })

    form = ProjectForm()
    return render(request, PROJECT_CREATE_TEMPLATE, {
        'form': form,
        'is_edit': False,
    })


@login_required
def edit_project_view(request, project_id):
    """Редактирование проекта."""
    project = get_object_or_404(Project, pk=project_id)

    if project.owner != request.user and not request.user.is_staff:
        return redirect(PROJECT_DETAIL_ROUTE, project_id=project_id)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect(PROJECT_DETAIL_ROUTE, project_id=project_id)
        return render(request, PROJECT_CREATE_TEMPLATE, {
            'form': form,
            'is_edit': True,
        })

    form = ProjectForm(instance=project)
    return render(request, PROJECT_CREATE_TEMPLATE, {
        'form': form,
        'is_edit': True,
    })


@login_required
@require_POST
def complete_project_view(request, project_id):
    """Завершить проект."""
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return JsonResponse(
            {'status': STATUS_ERROR, 'message': ERROR_PROJECT_NOT_FOUND},
            status=HTTPStatus.NOT_FOUND,
        )

    if project.owner != request.user and not request.user.is_staff:
        return JsonResponse(
            {'status': STATUS_ERROR},
            status=HTTPStatus.FORBIDDEN,
        )

    if project.status != PROJECT_STATUS_OPEN:
        return JsonResponse(
            {'status': STATUS_ERROR},
            status=HTTPStatus.BAD_REQUEST,
        )

    project.status = PROJECT_STATUS_CLOSED
    project.save()
    return JsonResponse({
        'status': STATUS_OK,
        'project_status': PROJECT_STATUS_CLOSED,
    })


@login_required
@require_POST
def toggle_participate_view(request, project_id):
    """Присоединиться / покинуть проект."""
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return JsonResponse(
            {'status': STATUS_ERROR, 'message': ERROR_PROJECT_NOT_FOUND},
            status=HTTPStatus.NOT_FOUND,
        )

    if project.owner == request.user:
        return JsonResponse(
            {'status': STATUS_ERROR},
            status=HTTPStatus.BAD_REQUEST,
        )

    is_participant = project.participants.filter(pk=request.user.pk).exists()

    if is_participant:
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)

    return JsonResponse({
        'status': STATUS_OK,
        'participant': not is_participant,
    })


@login_required
@require_POST
def toggle_favorite_view(request, project_id):
    """Добавить/убрать из избранного."""
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return JsonResponse(
            {'status': STATUS_ERROR, 'message': ERROR_PROJECT_NOT_FOUND},
            status=HTTPStatus.NOT_FOUND,
        )

    is_favorite = request.user.favorites.filter(pk=project.pk).exists()

    if is_favorite:
        request.user.favorites.remove(project)
    else:
        request.user.favorites.add(project)

    return JsonResponse({
        'status': STATUS_OK,
        'favorited': not is_favorite,
    })


@login_required
def favorites_view(request):
    """Избранные проекты."""
    projects_qs = (
        request.user.favorites
        .select_related('owner')
        .all()
        .order_by('-created_at')
    )
    page_obj = get_paginated_page(request, projects_qs)
    return render(request, FAVORITES_TEMPLATE, {
        'projects': page_obj,
        'page_obj': page_obj,
    })
