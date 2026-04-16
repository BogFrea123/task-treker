from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Task(models.Model):
    STATUS_CHOICES = [
        ('new', 'Нова'),
        ('in_progress', 'В процесі'),
        ('done', 'Виконана'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низький'),
        ('medium', 'Середній'),
        ('high', 'Високий'),
    ]

    title = models.CharField(max_length=200, verbose_name='Назва')
    description = models.TextField(blank=True, verbose_name='Опис')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Пріоритет'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Власник'
    )
    due_date = models.DateField(null=True, blank=True, verbose_name='Дедлайн')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачі'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.pk})

    def get_status_badge_class(self):
        return {
            'new': 'badge-secondary',
            'in_progress': 'badge-primary',
            'done': 'badge-success',
        }.get(self.status, 'badge-secondary')

    def get_priority_badge_class(self):
        return {
            'low': 'badge-info',
            'medium': 'badge-warning',
            'high': 'badge-danger',
        }.get(self.priority, 'badge-warning')
