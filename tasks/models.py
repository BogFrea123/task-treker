import re
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6366f1')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    class Meta:
        unique_together = ('name', 'owner')
    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    key = models.CharField(max_length=10)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    members = models.ManyToManyField(User, related_name='projects', blank=True)
    is_public = models.BooleanField(default=False, help_text='Публічний — будь-хто може бачити задачі')
    created_at = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=7, default='#7c3aed')
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f'[{self.key}] {self.name}'
    def get_absolute_url(self):
        return reverse('tasks:project_detail', kwargs={'pk': self.pk})


class Sprint(models.Model):
    STATUS_CHOICES = [('planned','Запланований'),('active','Активний'),('completed','Завершений')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
    name = models.CharField(max_length=100)
    goal = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_CHOICES = [('todo','To Do'),('in_progress','In Progress'),('review','Review'),('done','Done')]
    PRIORITY_CHOICES = [('low','Low'),('medium','Medium'),('high','High'),('urgent','Urgent')]
    TYPE_CHOICES = [('task','Task'),('bug','Bug'),('story','Story'),('epic','Epic')]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    issue_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='task')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    mentioned_users = models.ManyToManyField(User, blank=True, related_name='mentioned_in_tasks')
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.PositiveIntegerField(null=True, blank=True)
    logged_hours = models.PositiveIntegerField(default=0)
    # Фріланс-фіча: відкрита задача для всіх
    is_open_task = models.BooleanField(default=False, help_text='Відкрита задача — будь-хто може взятись')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        prefix = f'[{self.project.key}]' if self.project else ''
        return f'{prefix} {self.title}'

    def get_absolute_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.pk})

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.due_date and self.status != 'done':
            return self.due_date < timezone.now().date()
        return False

    def get_issue_number(self):
        return f'{self.project.key}-{self.pk}' if self.project else f'#{self.pk}'


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField()
    mentioned_users = models.ManyToManyField(User, blank=True, related_name='mentioned_in_comments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['created_at']
    def __str__(self):
        return f'Comment by {self.author} on {self.task}'
    def render_text(self):
        import html
        safe = html.escape(self.text)
        def repl(m):
            u = m.group(1)
            if User.objects.filter(username=u).exists():
                return f'<span class="mention">@{u}</span>'
            return m.group(0)
        return re.sub(r'@(\w+)', repl, safe)
