from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from .models import Project
from .forms import ProjectForm


def project_list_view(request):
    """Главная страница — список всех проектов."""
    projects_qs = Project.objects.all().order_by('-created_at')
    paginator = Paginator(projects_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'projects/project_list.html', {
        'projects': page_obj,
        'page_obj': page_obj,
    })


def project_detail_view(request, project_id):
    """Страница отдельного проекта."""
    project = get_object_or_404(Project, pk=project_id)
    return render(request, 'projects/project-details.html', {'project': project})


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
            return redirect(f'/projects/{project.pk}/')
        return render(request, 'projects/create-project.html', {
            'form': form,
            'is_edit': False,
        })

    form = ProjectForm()
    return render(request, 'projects/create-project.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def edit_project_view(request, project_id):
    """Редактирование проекта."""
    project = get_object_or_404(Project, pk=project_id)

    if project.owner != request.user and not request.user.is_staff:
        return redirect(f'/projects/{project_id}/')

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect(f'/projects/{project_id}/')
        return render(request, 'projects/create-project.html', {
            'form': form,
            'is_edit': True,
        })

    form = ProjectForm(instance=project)
    return render(request, 'projects/create-project.html', {
        'form': form,
        'is_edit': True,
    })


@login_required
@require_POST
def complete_project_view(request, project_id):
    """Завершить проект."""
    project = get_object_or_404(Project, pk=project_id)

    if project.owner != request.user and not request.user.is_staff:
        return JsonResponse({'status': 'error'}, status=403)

    if project.status != 'open':
        return JsonResponse({'status': 'error'}, status=400)

    project.status = 'closed'
    project.save()
    return JsonResponse({'status': 'ok', 'project_status': 'closed'})


@login_required
@require_POST
def toggle_participate_view(request, project_id):
    """Присоединиться / покинуть проект."""
    project = get_object_or_404(Project, pk=project_id)

    if project.owner == request.user:
        return JsonResponse({'status': 'error'}, status=400)

    if request.user in project.participants.all():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True

    return JsonResponse({'status': 'ok', 'participant': participant})


@login_required
@require_POST
def toggle_favorite_view(request, project_id):
    """Добавить/убрать из избранного."""
    project = get_object_or_404(Project, pk=project_id)
    if project in request.user.favorites.all():
        request.user.favorites.remove(project)
        favorited = False
    else:
        request.user.favorites.add(project)
        favorited = True
    return JsonResponse({'status': 'ok', 'favorited': favorited})


@login_required
def favorites_view(request):
    """Избранные проекты."""
    projects_qs = request.user.favorites.all().order_by('-created_at')
    paginator = Paginator(projects_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'projects/favorite_projects.html', {
        'projects': page_obj,
        'page_obj': page_obj,
    })