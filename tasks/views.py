from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                   DeleteView, FormView, TemplateView, View)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from .models import Task, Tag, Project, Sprint, Comment
from .forms import (TaskForm, TagForm, ProjectForm, SprintForm,
                    CommentForm, TaskFilterForm, RegisterForm)
from .mixins import UserIsOwnerMixin


# ───────── Landing ─────────
class LandingView(TemplateView):
    template_name = 'tasks/landing.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('tasks:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['demo_tasks'] = Task.objects.select_related('project', 'assignee').prefetch_related('tags')[:6]
        ctx['total_tasks'] = Task.objects.count()
        ctx['total_users'] = User.objects.count()
        ctx['total_projects'] = Project.objects.count()
        return ctx


# ───────── Auth ─────────
class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('tasks:dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('tasks:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


# ───────── Dashboard ─────────
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        my_tasks = Task.objects.filter(Q(owner=user) | Q(assignee=user)).distinct()
        ctx.update({
            'total': my_tasks.count(),
            'todo_count': my_tasks.filter(status='todo').count(),
            'in_progress_count': my_tasks.filter(status='in_progress').count(),
            'done_count': my_tasks.filter(status='done').count(),
            'overdue_count': my_tasks.filter(due_date__lt=today, status__in=['todo','in_progress','review']).count(),
            'recent_tasks': my_tasks.order_by('-updated_at')[:6],
            'urgent_tasks': my_tasks.filter(priority='urgent', status__in=['todo','in_progress']).order_by('due_date')[:5],
            'my_projects': (Project.objects.filter(Q(owner=user)|Q(members=user)).distinct().annotate(task_count=Count('tasks'))[:5]),
            'logged_hours': my_tasks.aggregate(total=Sum('logged_hours'))['total'] or 0,
        })
        return ctx


# ───────── Projects ─────────
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'tasks/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(Q(owner=user)|Q(members=user)).distinct().annotate(
            task_count=Count('tasks'),
            done_count=Count('tasks', filter=Q(tasks__status='done'))
        )


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'tasks/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(Q(owner=user)|Q(members=user)).distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.object
        ctx['sprints'] = project.sprints.annotate(task_count=Count('tasks'))
        ctx['backlog'] = project.tasks.filter(sprint__isnull=True).select_related('assignee').prefetch_related('tags')
        ctx['sprint_form'] = SprintForm()
        ctx['status_tabs'] = [
            ('todo', 'To Do', all_tasks.filter(status='todo').count(), '#6b7280'),
            ('in_progress', 'In Progress', all_tasks.filter(status='in_progress').count(), '#3b82f6'),
            ('review', 'Review', all_tasks.filter(status='review').count(), '#f59e0b'),
            ('done', 'Done', all_tasks.filter(status='done').count(), '#22c55e'),
        ]
        ctx['status_counts'] = {
            'todo': project.tasks.filter(status='todo').count(),
            'in_progress': project.tasks.filter(status='in_progress').count(),
            'review': project.tasks.filter(status='review').count(),
            'done': project.tasks.filter(status='done').count(),
        }
        return ctx


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'tasks/project_form.html'
    success_url = reverse_lazy('tasks:project_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['members'].queryset = User.objects.exclude(pk=self.request.user.pk)
        return form

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Новий проєкт'
        ctx['action'] = 'Створити'
        return ctx


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'tasks/project_form.html'

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['members'].queryset = User.objects.exclude(pk=self.request.user.pk)
        return form

    def get_success_url(self):
        return reverse_lazy('tasks:project_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Редагувати проєкт'
        ctx['action'] = 'Зберегти'
        return ctx


# ───────── Sprints ─────────
class SprintCreateView(LoginRequiredMixin, View):
    def post(self, request, project_pk):
        project = get_object_or_404(Project, pk=project_pk, owner=request.user)
        form = SprintForm(request.POST)
        if form.is_valid():
            sprint = form.save(commit=False)
            sprint.project = project
            sprint.save()
        return redirect('tasks:project_detail', pk=project_pk)


class SprintDetailView(LoginRequiredMixin, DetailView):
    model = Sprint
    template_name = 'tasks/sprint_detail.html'
    context_object_name = 'sprint'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sprint = self.object
        tasks = sprint.tasks.select_related('assignee').prefetch_related('tags')
        ctx['columns'] = [
            {'key': 'todo', 'label': 'To Do', 'color': '#6b7280', 'tasks': tasks.filter(status='todo')},
            {'key': 'in_progress', 'label': 'In Progress', 'color': '#3b82f6', 'tasks': tasks.filter(status='in_progress')},
            {'key': 'review', 'label': 'Review', 'color': '#f59e0b', 'tasks': tasks.filter(status='review')},
            {'key': 'done', 'label': 'Done', 'color': '#22c55e', 'tasks': tasks.filter(status='done')},
        ]
        ctx['total'] = tasks.count()
        ctx['done'] = tasks.filter(status='done').count()
        return ctx


# ───────── Tasks ─────────
class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.filter(Q(owner=user)|Q(assignee=user)).distinct()
        qs = qs.select_related('project','assignee','sprint').prefetch_related('tags')
        form = TaskFilterForm(user=user, data=self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('status'):
                qs = qs.filter(status=form.cleaned_data['status'])
            if form.cleaned_data.get('priority'):
                qs = qs.filter(priority=form.cleaned_data['priority'])
            if form.cleaned_data.get('issue_type'):
                qs = qs.filter(issue_type=form.cleaned_data['issue_type'])
            if form.cleaned_data.get('search'):
                qs = qs.filter(Q(title__icontains=form.cleaned_data['search'])|Q(description__icontains=form.cleaned_data['search']))
            a = form.cleaned_data.get('assignee')
            if a == 'me':
                qs = qs.filter(assignee=user)
            elif a:
                qs = qs.filter(assignee_id=a)
        tag_id = self.request.GET.get('tag')
        if tag_id:
            qs = qs.filter(tags__id=tag_id)
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        all_tasks = Task.objects.filter(Q(owner=user)|Q(assignee=user)).distinct()
        ctx['filter_form'] = TaskFilterForm(user=user, data=self.request.GET or None)
        ctx['user_tags'] = Tag.objects.filter(owner=user)
        ctx['user_projects'] = Project.objects.filter(Q(owner=user)|Q(members=user)).distinct()
        ctx['active_tag'] = self.request.GET.get('tag')
        ctx['active_project'] = self.request.GET.get('project')
        ctx['status_tabs'] = [
            ('todo', 'To Do', all_tasks.filter(status='todo').count(), '#6b7280'),
            ('in_progress', 'In Progress', all_tasks.filter(status='in_progress').count(), '#3b82f6'),
            ('review', 'Review', all_tasks.filter(status='review').count(), '#f59e0b'),
            ('done', 'Done', all_tasks.filter(status='done').count(), '#22c55e'),
        ]
        ctx['status_counts'] = {
            'all': all_tasks.count(),
            'todo': all_tasks.filter(status='todo').count(),
            'in_progress': all_tasks.filter(status='in_progress').count(),
            'review': all_tasks.filter(status='review').count(),
            'done': all_tasks.filter(status='done').count(),
        }
        return ctx


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(Q(owner=user)|Q(assignee=user)|Q(project__members=user)).distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comments'] = self.object.comments.select_related('author')
        ctx['comment_form'] = CommentForm()
        return ctx

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        form = CommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.task = task
            c.author = request.user
            c.save()
        # Handle log hours
        log_h = request.POST.get('log_hours')
        if log_h:
            try:
                task.logged_hours += int(log_h)
                task.save()
            except ValueError:
                pass
        return redirect('tasks:task_detail', pk=task.pk)


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['user'] = self.request.user
        return kw

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Створити'
        ctx['page_title'] = 'Нова задача'
        return ctx


class TaskUpdateView(LoginRequiredMixin, UserIsOwnerMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['user'] = self.request.user
        return kw

    def get_success_url(self):
        return reverse_lazy('tasks:task_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Зберегти'
        ctx['page_title'] = 'Редагування'
        return ctx


class TaskDeleteView(LoginRequiredMixin, UserIsOwnerMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')
    context_object_name = 'task'


class TaskUpdateStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        user = request.user
        if task.owner != user and task.assignee != user:
            return JsonResponse({'ok': False}, status=403)
        status = request.POST.get('status')
        if status in dict(Task.STATUS_CHOICES):
            task.status = status
            task.save()
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False}, status=400)


class CommentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk, author=request.user)
        task_pk = comment.task.pk
        comment.delete()
        return redirect('tasks:task_detail', pk=task_pk)


# ───────── Kanban ─────────
class KanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/kanban.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        tasks = Task.objects.filter(Q(owner=user)|Q(assignee=user)).distinct()
        tasks = tasks.select_related('project','assignee').prefetch_related('tags')
        ctx['columns'] = [
            {'key': 'todo',        'label': 'To Do',       'color': '#6b7280', 'tasks': tasks.filter(status='todo')},
            {'key': 'in_progress', 'label': 'In Progress', 'color': '#3b82f6', 'tasks': tasks.filter(status='in_progress')},
            {'key': 'review',      'label': 'Review',      'color': '#f59e0b', 'tasks': tasks.filter(status='review')},
            {'key': 'done',        'label': 'Done',        'color': '#22c55e', 'tasks': tasks.filter(status='done')},
        ]
        return ctx


# ───────── Tags ─────────
class TagListView(LoginRequiredMixin, ListView):
    model = Tag
    template_name = 'tasks/tag_list.html'
    context_object_name = 'tags'

    def get_queryset(self):
        return Tag.objects.filter(owner=self.request.user).annotate(task_count=Count('tasks'))


class TagCreateView(LoginRequiredMixin, CreateView):
    model = Tag
    form_class = TagForm
    template_name = 'tasks/tag_form.html'
    success_url = reverse_lazy('tasks:tag_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class TagDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        tag = get_object_or_404(Tag, pk=pk, owner=request.user)
        tag.delete()
        return redirect('tasks:tag_list')
