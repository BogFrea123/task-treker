from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task, Tag, Project, Sprint, Comment


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'issue_type', 'status', 'priority', 'project', 'sprint', 'assignee', 'tags', 'due_date', 'estimated_hours']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'cu-input', 'placeholder': 'Назва задачі...'}),
            'description': forms.Textarea(attrs={'class': 'cu-input', 'rows': 4, 'placeholder': 'Опис...'}),
            'issue_type': forms.Select(attrs={'class': 'cu-select'}),
            'status': forms.Select(attrs={'class': 'cu-select'}),
            'priority': forms.Select(attrs={'class': 'cu-select'}),
            'project': forms.Select(attrs={'class': 'cu-select'}),
            'sprint': forms.Select(attrs={'class': 'cu-select'}),
            'assignee': forms.Select(attrs={'class': 'cu-select'}),
            'tags': forms.CheckboxSelectMultiple(),
            'due_date': forms.DateInput(attrs={'class': 'cu-input', 'type': 'date'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'cu-input', 'placeholder': '0', 'min': 0}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            user_projects = Project.objects.filter(members=user) | Project.objects.filter(owner=user)
            user_projects = user_projects.distinct()
            self.fields['project'].queryset = user_projects
            self.fields['sprint'].queryset = Sprint.objects.filter(project__in=user_projects)
            self.fields['tags'].queryset = Tag.objects.filter(owner=user)
            self.fields['assignee'].queryset = User.objects.filter(
                id__in=user_projects.values_list('members', flat=True)
            ) | User.objects.filter(id__in=user_projects.values_list('owner', flat=True))
            self.fields['assignee'].queryset = self.fields['assignee'].queryset.distinct()
        self.fields['project'].required = False
        self.fields['sprint'].required = False
        self.fields['assignee'].required = False
        self.fields['tags'].required = False
        self.fields['due_date'].required = False
        self.fields['estimated_hours'].required = False


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'cu-input', 'rows': 3, 'placeholder': 'Додати коментар...'}),
        }
        labels = {'text': ''}


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'key', 'description', 'color', 'members']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'cu-input', 'placeholder': 'Назва проєкту'}),
            'key': forms.TextInput(attrs={'class': 'cu-input', 'placeholder': 'PROJ', 'maxlength': '10', 'style': 'text-transform:uppercase'}),
            'description': forms.Textarea(attrs={'class': 'cu-input', 'rows': 3}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'cu-color-input'}),
            'members': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['members'].required = False
        self.fields['description'].required = False

    def clean_key(self):
        return self.cleaned_data['key'].upper()


class SprintForm(forms.ModelForm):
    class Meta:
        model = Sprint
        fields = ['name', 'goal', 'status', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'cu-input', 'placeholder': 'Sprint 1'}),
            'goal': forms.Textarea(attrs={'class': 'cu-input', 'rows': 2, 'placeholder': 'Мета спринту...'}),
            'status': forms.Select(attrs={'class': 'cu-select'}),
            'start_date': forms.DateInput(attrs={'class': 'cu-input', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'cu-input', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['goal'].required = False
        self.fields['start_date'].required = False
        self.fields['end_date'].required = False


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'cu-input', 'placeholder': 'Назва тегу'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'cu-color-input'}),
        }


class TaskFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'Статус')] + Task.STATUS_CHOICES
    PRIORITY_CHOICES = [('', 'Пріоритет')] + Task.PRIORITY_CHOICES
    TYPE_CHOICES = [('', 'Тип')] + Task.TYPE_CHOICES

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'cu-select-sm'}))
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'cu-select-sm'}))
    issue_type = forms.ChoiceField(choices=TYPE_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'cu-select-sm'}))
    search = forms.CharField(required=False,
        widget=forms.TextInput(attrs={'class': 'cu-input-sm', 'placeholder': 'Пошук...'}))
    assignee = forms.ChoiceField(required=False,
        widget=forms.Select(attrs={'class': 'cu-select-sm'}))

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            members = User.objects.filter(projects__in=Project.objects.filter(owner=user)).distinct()
            choices = [('', 'Виконавець'), ('me', 'Мої')] + [(u.id, u.username) for u in members]
            self.fields['assignee'].choices = choices


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False,
        widget=forms.EmailInput(attrs={'class': 'cu-input', 'placeholder': 'Email (необов\'язково)'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['username', 'password1', 'password2']:
            self.fields[f].widget.attrs['class'] = 'cu-input'
        self.fields['username'].widget.attrs['placeholder'] = 'Логін'
        self.fields['password1'].widget.attrs['placeholder'] = 'Пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторіть пароль'
        for f in ['username', 'password1', 'password2']:
            self.fields[f].help_text = None
        self.fields['username'].label = 'Логін'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Підтвердження'
