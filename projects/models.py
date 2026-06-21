from django.conf import settings
from django.db import models


PROJECT_NAME_MAX_LENGTH = 200
PROJECT_STATUS_MAX_LENGTH = 6

PROJECT_STATUS_OPEN = "open"
PROJECT_STATUS_CLOSED = "closed"

PROJECT_STATUS_CHOICES = [
    (PROJECT_STATUS_OPEN, "Open"),
    (PROJECT_STATUS_CLOSED, "Closed"),
]


class Project(models.Model):
    """Модель проекта."""

    name = models.CharField(
        max_length=PROJECT_NAME_MAX_LENGTH,
        verbose_name="Название",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    github_url = models.URLField(
        blank=True,
        verbose_name="GitHub",
    )
    status = models.CharField(
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=PROJECT_STATUS_CHOICES,
        default=PROJECT_STATUS_OPEN,
        verbose_name="Статус",
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="participated_projects",
        verbose_name="Участники",
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
