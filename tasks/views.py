from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404, redirect

from .models import Task, Tag
from .forms import TaskForm, TagForm, TaskFilterForm, RegisterForm
from .mixins import UserIsOwnerMixin


class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('tasks:task_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('tasks:task_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tasks = Task.objects.filter(owner=user)
        from django.utils import timezone
        today = timezone.now().date()
        context.update({
            'total': tasks.count(),
            'todo_count': tasks.filter(status='todo').count(),
            'in_progress_count': tasks.filter(status='in_progress').count(),
            'done_count': tasks.filter(status='done').count(),
            'overdue_count': tasks.filter(due_date__lt=today, status__in=['todo','in_progress','review']).count(),
            'recent_tasks': tasks.order_by('-created_at')[:5],
            'urgent_tasks': tasks.filter(priority='urgent', status__in=['todo','in_progress']).order_by('due_date')[:5],
        })
        return context


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        queryset = Task.objects.filter(owner=self.request.user).prefetch_related('tags')
        form = TaskFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            if form.cleaned_data.get('priority'):
                queryset = queryset.filter(priority=form.cleaned_data['priority'])
            if form.cleaned_data.get('search'):
                queryset = queryset.filter(
                    Q(title__icontains=form.cleaned_data['search']) |
                    Q(description__icontains=form.cleaned_data['search'])
                )
        tag_id = self.request.GET.get('tag')
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        all_tasks = Task.objects.filter(owner=user)
        context['filter_form'] = TaskFilterForm(self.request.GET or None)
        context['user_tags'] = Tag.objects.filter(owner=user)
        context['active_tag'] = self.request.GET.get('tag')
        context['status_counts'] = {
            'todo': all_tasks.filter(status='todo').count(),
            'in_progress': all_tasks.filter(status='in_progress').count(),
            'review': all_tasks.filter(status='review').count(),
            'done': all_tasks.filter(status='done').count(),
        }
        return context


class KanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/kanban.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tasks = Task.objects.filter(owner=user).prefetch_related('tags')
        context['columns'] = [
            {'key': 'todo', 'label': 'To Do', 'color': '#7c3aed', 'tasks': tasks.filter(status='todo')},
            {'key': 'in_progress', 'label': 'In Progress', 'color': '#2563eb', 'tasks': tasks.filter(status='in_progress')},
            {'key': 'review', 'label': 'Review', 'color': '#d97706', 'tasks': tasks.filter(status='review')},
            {'key': 'done', 'label': 'Done', 'color': '#16a34a', 'tasks': tasks.filter(status='done')},
        ]
        return context


class TaskUpdateStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, owner=request.user)
        status = request.POST.get('status')
        if status in dict(Task.STATUS_CHOICES):
            task.status = status
            task.save()
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False}, status=400)


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user).prefetch_related('tags')


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Створити'
        context['page_title'] = 'Нова задача'
        return context


class TaskUpdateView(LoginRequiredMixin, UserIsOwnerMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy('tasks:task_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Зберегти'
        context['page_title'] = f'Редагування'
        return context


class TaskDeleteView(LoginRequiredMixin, UserIsOwnerMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')
    context_object_name = 'task'


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
