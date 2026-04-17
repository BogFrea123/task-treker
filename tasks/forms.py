from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task, Tag


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'tags', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'cu-input', 'placeholder': 'Назва задачі...'}),
            'description': forms.Textarea(attrs={'class': 'cu-input', 'rows': 4, 'placeholder': 'Додати опис...'}),
            'status': forms.Select(attrs={'class': 'cu-select'}),
            'priority': forms.Select(attrs={'class': 'cu-select'}),
            'tags': forms.CheckboxSelectMultiple(attrs={'class': 'cu-checkbox-group'}),
            'due_date': forms.DateInput(attrs={'class': 'cu-input', 'type': 'date'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['tags'].queryset = Tag.objects.filter(owner=user)


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'cu-input', 'placeholder': 'Назва тегу...'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'cu-color-input'}),
        }


class TaskFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'Всі статуси')] + Task.STATUS_CHOICES
    PRIORITY_CHOICES = [('', 'Всі пріоритети')] + Task.PRIORITY_CHOICES

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'cu-select-sm'}))
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'cu-select-sm'}))
    search = forms.CharField(required=False,
        widget=forms.TextInput(attrs={'class': 'cu-input-sm', 'placeholder': 'Пошук...'}))


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False,
        widget=forms.EmailInput(attrs={'class': 'cu-input', 'placeholder': 'Email (необов\'язково)'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['username', 'password1', 'password2']:
            self.fields[field].widget.attrs['class'] = 'cu-input'
        self.fields['username'].widget.attrs['placeholder'] = 'Логін'
        self.fields['password1'].widget.attrs['placeholder'] = 'Пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторіть пароль'
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        self.fields['username'].label = 'Логін'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Підтвердження'
