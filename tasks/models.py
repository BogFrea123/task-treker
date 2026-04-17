from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name='Назва')
    color = models.CharField(max_length=7, default='#6366f1', verbose_name='Колір')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        unique_together = ('name', 'owner')

    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=200, verbose_name='Назва')
    description = models.TextField(blank=True, verbose_name='Опис')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name='Статус')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='Пріоритет')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks', verbose_name='Власник')
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks', verbose_name='Теги')
    due_date = models.DateField(null=True, blank=True, verbose_name='Дедлайн')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачі'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.pk})

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.due_date and self.status != 'done':
            return self.due_date < timezone.now().date()
        return False
