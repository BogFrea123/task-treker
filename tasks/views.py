import re
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
                    CommentForm, ReplyForm, TaskFilterForm, RegisterForm)
from .mixins import UserIsOwnerMixin


def extract_mentions(text):
    usernames = re.findall(r'@(\w+)', text)
    return User.objects.filter(username__in=usernames) if usernames else User.objects.none()


# ── Landing ──────────────────────────────────────────
class LandingView(TemplateView):
    template_name = 'tasks/landing.html'
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('tasks:dashboard')
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['open_tasks'] = Task.objects.filter(is_open_task=True).select_related('project','owner').prefetch_related('tags')[:8]
        ctx['public_projects'] = Project.objects.filter(is_public=True).annotate(task_count=Count('tasks'))[:6]
        ctx['total_tasks'] = Task.objects.count()
        ctx['total_users'] = User.objects.count()
        ctx['total_projects'] = Project.objects.count()
        return ctx


# ── Auth ─────────────────────────────────────────────
class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('tasks:dashboard')
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('tasks:dashboard')
        return super().dispatch(request, *args, **kwargs)
    def form_valid(self, form):
        login(self.request, form.save())
        return super().form_valid(form)


# ── Dashboard ─────────────────────────────────────────
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/dashboard.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        my = Task.objects.filter(Q(owner=user)|Q(assignee=user)).distinct()
        ctx.update({
            'total': my.count(),
            'todo_count': my.filter(status='todo').count(),
            'in_progress_count': my.filter(status='in_progress').count(),
            'done_count': my.filter(status='done').count(),
            'overdue_count': my.filter(due_date__lt=today, status__in=['todo','in_progress','review']).count(),
            'recent_tasks': my.order_by('-updated_at')[:6],
            'urgent_tasks': my.filter(priority='urgent', status__in=['todo','in_progress']).order_by('due_date')[:5],
            'my_projects': Project.objects.filter(Q(owner=user)|Q(members=user)).distinct().annotate(task_count=Count('tasks'))[:5],
            'logged_hours': my.aggregate(t=Sum('logged_hours'))['t'] or 0,
            'mentioned_tasks': Task.objects.filter(mentioned_users=user).order_by('-created_at')[:4],
            'my_companies_dash': Company.objects.filter(Q(owner=user) | Q(memberships__user=user, memberships__status='approved')).distinct()[:4],
            'pending_apps_count': CompanyMembership.objects.filter(company__owner=user, status='pending').count(),
        })
        return ctx


# ── Public Board (з фільтрацією) ──────────────────────
class PublicBoardView(TemplateView):
    template_name = 'tasks/public_board.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        GET = self.request.GET

        qs = Task.objects.filter(is_open_task=True).select_related(
            'project', 'owner', 'assignee'
        ).prefetch_related('tags')

        # Фільтрація
        priority = GET.get('priority', '')
        issue_type = GET.get('issue_type', '')
        search = GET.get('search', '')
        project_id = GET.get('project', '')
        only_free = GET.get('only_free', '')

        if priority:
            qs = qs.filter(priority=priority)
        if issue_type:
            qs = qs.filter(issue_type=issue_type)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        if project_id:
            qs = qs.filter(project_id=project_id)
        if only_free:
            qs = qs.filter(assignee__isnull=True)

        ctx['open_tasks'] = qs.order_by('-created_at')
        ctx['public_projects'] = Project.objects.filter(
            is_public=True
        ).annotate(
            task_count=Count('tasks'),
            done_count=Count('tasks', filter=Q(tasks__status='done'))
        )
        # Для фільтрів
        ctx['priority_choices'] = Task.PRIORITY_CHOICES
        ctx['type_choices'] = Task.TYPE_CHOICES
        ctx['all_projects'] = Project.objects.filter(is_public=True)
        ctx['selected_priority'] = priority
        ctx['selected_type'] = issue_type
        ctx['selected_project'] = project_id
        ctx['search_query'] = search
        ctx['only_free'] = only_free
        ctx['total_count'] = qs.count()
        ctx['free_count'] = qs.filter(assignee__isnull=True).count()
        return ctx


class TakeTaskView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, is_open_task=True)
        if not task.assignee:
            task.assignee = request.user
            task.status = 'in_progress'
            task.save()
        return redirect('tasks:task_detail', pk=pk)


# ── Projects ──────────────────────────────────────────
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'tasks/project_list.html'
    context_object_name = 'projects'
    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(Q(owner=user)|Q(members=user)).distinct().annotate(
            task_count=Count('tasks'), done_count=Count('tasks', filter=Q(tasks__status='done')))


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'tasks/project_detail.html'
    context_object_name = 'project'
    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(Q(owner=user)|Q(members=user)).distinct()
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        p = self.object
        ctx['sprints'] = p.sprints.annotate(task_count=Count('tasks'))
        ctx['backlog'] = p.tasks.filter(sprint__isnull=True).select_related('assignee').prefetch_related('tags')
        ctx['sprint_form'] = SprintForm()
        ctx['status_counts'] = {s: p.tasks.filter(status=s).count() for s in ['todo','in_progress','review','done']}
        return ctx


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project; form_class = ProjectForm
    template_name = 'tasks/project_form.html'
    success_url = reverse_lazy('tasks:project_list')
    def get_form(self, fc=None):
        f = super().get_form(fc); f.fields['members'].queryset = User.objects.exclude(pk=self.request.user.pk); return f
    def form_valid(self, form):
        form.instance.owner = self.request.user; return super().form_valid(form)
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs); ctx['page_title']='Новий проєкт'; ctx['action']='Створити'; return ctx


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project; form_class = ProjectForm
    template_name = 'tasks/project_form.html'
    def get_queryset(self): return Project.objects.filter(owner=self.request.user)
    def get_form(self, fc=None):
        f = super().get_form(fc); f.fields['members'].queryset = User.objects.exclude(pk=self.request.user.pk); return f
    def get_success_url(self): return reverse_lazy('tasks:project_detail', kwargs={'pk': self.object.pk})
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs); ctx['page_title']='Редагувати'; ctx['action']='Зберегти'; return ctx


# ── Sprints ───────────────────────────────────────────
class SprintCreateView(LoginRequiredMixin, View):
    def post(self, request, project_pk):
        project = get_object_or_404(Project, pk=project_pk)
        if project.owner != request.user and not project.members.filter(pk=request.user.pk).exists():
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        form = SprintForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False); s.project = project; s.save()
        return redirect('tasks:project_detail', pk=project_pk)


class SprintDetailView(LoginRequiredMixin, DetailView):
    model = Sprint; template_name = 'tasks/sprint_detail.html'; context_object_name = 'sprint'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tasks = self.object.tasks.select_related('assignee').prefetch_related('tags')
        ctx['columns'] = [
            {'key':'todo','label':'To Do','color':'#6b7280','tasks':tasks.filter(status='todo')},
            {'key':'in_progress','label':'In Progress','color':'#3b82f6','tasks':tasks.filter(status='in_progress')},
            {'key':'review','label':'Review','color':'#f59e0b','tasks':tasks.filter(status='review')},
            {'key':'done','label':'Done','color':'#22c55e','tasks':tasks.filter(status='done')},
        ]
        ctx['total'] = tasks.count(); ctx['done'] = tasks.filter(status='done').count()
        return ctx


# ── Tasks ─────────────────────────────────────────────
class TaskListView(LoginRequiredMixin, ListView):
    model = Task; template_name = 'tasks/task_list.html'; context_object_name = 'tasks'; paginate_by = 25
    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.filter(Q(owner=user)|Q(assignee=user)).distinct()
        qs = qs.select_related('project','assignee','sprint').prefetch_related('tags')
        form = TaskFilterForm(data=self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('status'): qs = qs.filter(status=form.cleaned_data['status'])
            if form.cleaned_data.get('priority'): qs = qs.filter(priority=form.cleaned_data['priority'])
            if form.cleaned_data.get('issue_type'): qs = qs.filter(issue_type=form.cleaned_data['issue_type'])
            if form.cleaned_data.get('search'):
                q = form.cleaned_data['search']
                qs = qs.filter(Q(title__icontains=q)|Q(description__icontains=q))
        if self.request.GET.get('tag'): qs = qs.filter(tags__id=self.request.GET['tag'])
        if self.request.GET.get('project'): qs = qs.filter(project_id=self.request.GET['project'])
        return qs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        all_t = Task.objects.filter(Q(owner=user)|Q(assignee=user)).distinct()
        ctx['filter_form'] = TaskFilterForm(data=self.request.GET or None)
        ctx['user_tags'] = Tag.objects.filter(owner=user)
        ctx['user_projects'] = Project.objects.filter(Q(owner=user)|Q(members=user)).distinct()
        ctx['active_tag'] = self.request.GET.get('tag')
        ctx['status_tabs'] = [
            ('todo','To Do',all_t.filter(status='todo').count(),'#6b7280'),
            ('in_progress','In Progress',all_t.filter(status='in_progress').count(),'#3b82f6'),
            ('review','Review',all_t.filter(status='review').count(),'#f59e0b'),
            ('done','Done',all_t.filter(status='done').count(),'#22c55e'),
        ]
        return ctx


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task; template_name = 'tasks/task_detail.html'; context_object_name = 'task'
    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            Q(owner=user)|Q(assignee=user)|Q(project__members=user)|Q(is_open_task=True)
        ).distinct()
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comments'] = self.object.comments.filter(parent__isnull=True).select_related('author').prefetch_related('replies__author','replies__mentioned_users','mentioned_users')
        ctx['comment_form'] = CommentForm()
        ctx['reply_form'] = ReplyForm()
        ctx['all_users'] = list(User.objects.values_list('username', flat=True))
        return ctx
    def post(self, request, *args, **kwargs):
        task = self.get_object()
        if 'log_hours' in request.POST:
            try:
                h = int(request.POST['log_hours'])
                if h > 0: task.logged_hours += h; task.save()
            except ValueError: pass
            return redirect('tasks:task_detail', pk=task.pk)
        if 'parent_id' in request.POST:
            parent = get_object_or_404(Comment, pk=request.POST['parent_id'], task=task)
            form = ReplyForm(request.POST)
            if form.is_valid():
                r = form.save(commit=False); r.task=task; r.author=request.user; r.parent=parent; r.save()
                r.mentioned_users.set(extract_mentions(r.text))
            return redirect('tasks:task_detail', pk=task.pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False); c.task=task; c.author=request.user; c.save()
            c.mentioned_users.set(extract_mentions(c.text))
        return redirect('tasks:task_detail', pk=task.pk)


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task; form_class = TaskForm; template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')
    def get_form_kwargs(self):
        kw = super().get_form_kwargs(); kw['user'] = self.request.user; return kw
    def form_valid(self, form):
        form.instance.owner = self.request.user
        resp = super().form_valid(form)
        if form.cleaned_data.get('mention_users'):
            self.object.mentioned_users.set(form.cleaned_data['mention_users'])
        desc_m = extract_mentions(form.instance.description)
        if desc_m.exists(): self.object.mentioned_users.add(*desc_m)
        return resp
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs); ctx['action']='Створити'; ctx['page_title']='Нова задача'
        ctx['all_users'] = list(User.objects.values_list('username', flat=True)); return ctx


class TaskUpdateView(LoginRequiredMixin, UserIsOwnerMixin, UpdateView):
    model = Task; form_class = TaskForm; template_name = 'tasks/task_form.html'
    def get_form_kwargs(self):
        kw = super().get_form_kwargs(); kw['user'] = self.request.user; return kw
    def form_valid(self, form):
        resp = super().form_valid(form)
        if form.cleaned_data.get('mention_users') is not None:
            self.object.mentioned_users.set(form.cleaned_data['mention_users'])
        return resp
    def get_success_url(self): return reverse_lazy('tasks:task_detail', kwargs={'pk': self.object.pk})
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs); ctx['action']='Зберегти'; ctx['page_title']='Редагування'
        ctx['all_users'] = list(User.objects.values_list('username', flat=True)); return ctx


class TaskDeleteView(LoginRequiredMixin, UserIsOwnerMixin, DeleteView):
    model = Task; template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list'); context_object_name = 'task'


class TaskUpdateStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        if task.owner != request.user and task.assignee != request.user:
            return JsonResponse({'ok': False}, status=403)
        s = request.POST.get('status')
        if s in dict(Task.STATUS_CHOICES):
            task.status = s; task.save()
            return JsonResponse({'ok': True, 'status': s, 'label': dict(Task.STATUS_CHOICES)[s]})
        return JsonResponse({'ok': False}, status=400)


# ── Comments ──────────────────────────────────────────
class CommentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        c = get_object_or_404(Comment, pk=pk, author=request.user)
        task_pk = c.task.pk; c.delete()
        return redirect('tasks:task_detail', pk=task_pk)


# ── Kanban ────────────────────────────────────────────
class KanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/kanban.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        tasks = Task.objects.filter(Q(owner=user)|Q(assignee=user)).distinct().select_related('project','assignee').prefetch_related('tags')
        ctx['columns'] = [
            {'key':'todo','label':'To Do','color':'#6b7280','tasks':tasks.filter(status='todo')},
            {'key':'in_progress','label':'In Progress','color':'#3b82f6','tasks':tasks.filter(status='in_progress')},
            {'key':'review','label':'Review','color':'#f59e0b','tasks':tasks.filter(status='review')},
            {'key':'done','label':'Done','color':'#22c55e','tasks':tasks.filter(status='done')},
        ]
        return ctx


# ── Tags ──────────────────────────────────────────────
class TagListView(LoginRequiredMixin, ListView):
    model = Tag; template_name = 'tasks/tag_list.html'; context_object_name = 'tags'
    def get_queryset(self): return Tag.objects.filter(owner=self.request.user).annotate(task_count=Count('tasks'))

class TagCreateView(LoginRequiredMixin, CreateView):
    model = Tag; form_class = TagForm; template_name = 'tasks/tag_form.html'
    success_url = reverse_lazy('tasks:tag_list')
    def form_valid(self, form): form.instance.owner = self.request.user; return super().form_valid(form)

class TagDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        get_object_or_404(Tag, pk=pk, owner=request.user).delete()
        return redirect('tasks:tag_list')


# ── API ───────────────────────────────────────────────
class UserSearchView(LoginRequiredMixin, View):
    def get(self, request):
        q = request.GET.get('q', '')
        users = list(User.objects.filter(username__icontains=q).values('id','username')[:10])
        return JsonResponse({'users': users})


# ── Companies ──────────────────────────────────────────
from .models import Company, CompanyMembership
from .forms import CompanyForm, MembershipApplicationForm, MembershipReviewForm


class CompanyCatalogView(TemplateView):
    template_name = 'tasks/company_catalog.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = Company.objects.all().annotate(
            approved_count=Count('memberships', filter=Q(memberships__status='approved'))
        )
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(username__icontains=search) | Q(description__icontains=search))
        ctx['companies'] = qs.order_by('-created_at')
        ctx['search'] = search
        ctx['my_companies'] = []
        ctx['my_applications'] = []
        if self.request.user.is_authenticated:
            ctx['my_companies'] = Company.objects.filter(
                Q(owner=self.request.user) |
                Q(memberships__user=self.request.user, memberships__status='approved')
            ).distinct()
            ctx['my_applications'] = CompanyMembership.objects.filter(
                user=self.request.user
            ).select_related('company').order_by('-created_at')
        return ctx


class CompanyDetailView(DetailView):
    model = Company
    template_name = 'tasks/company_detail.html'
    context_object_name = 'company'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        company = self.object
        user = self.request.user
        ctx['members'] = company.memberships.filter(status='approved').select_related('user')
        ctx['is_owner'] = user.is_authenticated and (company.owner == user or user.is_staff)
        ctx['is_member'] = user.is_authenticated and company.memberships.filter(user=user, status='approved').exists()
        ctx['my_application'] = None
        if user.is_authenticated:
            ctx['my_application'] = company.memberships.filter(user=user).first()
        # Pending applications for owner/admin
        if ctx['is_owner']:
            ctx['pending'] = company.memberships.filter(status='pending').select_related('user')
        return ctx


class CompanyCreateView(LoginRequiredMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'tasks/company_form.html'
    success_url = reverse_lazy('tasks:company_catalog')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        # Owner automatically becomes approved member
        CompanyMembership.objects.create(
            company=self.object,
            user=self.request.user,
            display_name=self.request.user.username,
            tag='Засновник',
            motivation='Створив компанію',
            status='approved',
        )
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Створити компанію'
        return ctx


class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'tasks/company_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.owner != request.user and not request.user.is_staff:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('tasks:company_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Редагувати компанію'
        return ctx


class CompanyApplyView(LoginRequiredMixin, View):
    """Відправити квиток (заявку) на вступ"""

    def get(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        existing = CompanyMembership.objects.filter(company=company, user=request.user).first()
        if existing:
            return redirect('tasks:company_detail', pk=pk)
        form = MembershipApplicationForm()
        return render(request, 'tasks/company_apply.html', {'company': company, 'form': form})

    def post(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        if company.owner == request.user:
            return redirect('tasks:company_detail', pk=pk)
        existing = CompanyMembership.objects.filter(company=company, user=request.user).first()
        if existing:
            return redirect('tasks:company_detail', pk=pk)
        form = MembershipApplicationForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.company = company
            m.user = request.user
            m.save()
            return redirect('tasks:company_detail', pk=pk)
        return render(request, 'tasks/company_apply.html', {'company': company, 'form': form})


class MembershipReviewView(LoginRequiredMixin, View):
    """Власник або адмін приймає / відхиляє заявку"""

    def post(self, request, pk):
        membership = get_object_or_404(CompanyMembership, pk=pk)
        company = membership.company
        if company.owner != request.user and not request.user.is_staff:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        action = request.POST.get('action')
        from django.utils import timezone
        if action == 'approve':
            membership.status = 'approved'
            membership.reviewed_by = request.user
            membership.reviewed_at = timezone.now()
            membership.save()
        elif action == 'reject':
            membership.status = 'rejected'
            membership.reject_reason = request.POST.get('reject_reason', '')
            membership.reviewed_by = request.user
            membership.reviewed_at = timezone.now()
            membership.save()
        return redirect('tasks:company_detail', pk=company.pk)


class MembershipKickView(LoginRequiredMixin, View):
    """Видалити учасника з компанії"""

    def post(self, request, pk):
        membership = get_object_or_404(CompanyMembership, pk=pk)
        company = membership.company
        if company.owner != request.user and not request.user.is_staff:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        if membership.user != company.owner:
            membership.delete()
        return redirect('tasks:company_detail', pk=company.pk)


class MembershipLeaveView(LoginRequiredMixin, View):
    """Вийти з компанії"""

    def post(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        if company.owner == request.user:
            return redirect('tasks:company_detail', pk=pk)
        CompanyMembership.objects.filter(company=company, user=request.user).delete()
        return redirect('tasks:company_catalog')


# Helper for render shortcut
from django.shortcuts import render
