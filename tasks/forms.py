from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task, Tag, Project, Sprint, Comment


class TaskForm(forms.ModelForm):
    mention_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple(), label='Тегнути користувачів')

    class Meta:
        model = Task
        fields = ['title','description','issue_type','status','priority','project','sprint',
                  'assignee','tags','due_date','estimated_hours','is_open_task','mention_users']
        widgets = {
            'title': forms.TextInput(attrs={'class':'cu-input','placeholder':'Назва задачі...'}),
            'description': forms.Textarea(attrs={'class':'cu-input','rows':4,'placeholder':'Опис... @username щоб тегнути','id':'desc-ta'}),
            'issue_type': forms.Select(attrs={'class':'cu-select'}),
            'status': forms.Select(attrs={'class':'cu-select'}),
            'priority': forms.Select(attrs={'class':'cu-select'}),
            'project': forms.Select(attrs={'class':'cu-select'}),
            'sprint': forms.Select(attrs={'class':'cu-select'}),
            'assignee': forms.Select(attrs={'class':'cu-select'}),
            'tags': forms.CheckboxSelectMultiple(),
            'due_date': forms.DateInput(attrs={'class':'cu-input','type':'date'}),
            'estimated_hours': forms.NumberInput(attrs={'class':'cu-input','placeholder':'0','min':0}),
            'is_open_task': forms.CheckboxInput(attrs={'class':'cu-checkbox'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            ups = (Project.objects.filter(members=user)|Project.objects.filter(owner=user)).distinct()
            self.fields['project'].queryset = ups
            self.fields['sprint'].queryset = Sprint.objects.filter(project__in=ups)
            self.fields['tags'].queryset = Tag.objects.filter(owner=user)
            all_m = (User.objects.filter(id__in=ups.values_list('members',flat=True))|
                     User.objects.filter(id__in=ups.values_list('owner',flat=True))).distinct()
            self.fields['assignee'].queryset = all_m
            self.fields['mention_users'].queryset = User.objects.exclude(pk=user.pk)
        if self.instance and self.instance.pk:
            self.fields['mention_users'].initial = self.instance.mentioned_users.all()
        for f in ['project','sprint','assignee','tags','due_date','estimated_hours','mention_users']:
            self.fields[f].required = False


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {'text': forms.Textarea(attrs={'class':'cu-input','rows':3,'placeholder':'Коментар... @username щоб тегнути','id':'comment-ta'})}
        labels = {'text': ''}


class ReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {'text': forms.Textarea(attrs={'class':'cu-input','rows':2,'placeholder':'Відповідь...'})}
        labels = {'text': ''}


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name','key','description','color','is_public','members']
        widgets = {
            'name': forms.TextInput(attrs={'class':'cu-input','placeholder':'Назва проєкту'}),
            'key': forms.TextInput(attrs={'class':'cu-input','placeholder':'PROJ','maxlength':'10'}),
            'description': forms.Textarea(attrs={'class':'cu-input','rows':3}),
            'color': forms.TextInput(attrs={'type':'color'}),
            'is_public': forms.CheckboxInput(attrs={'class':'cu-checkbox'}),
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
        fields = ['name','goal','status','start_date','end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class':'cu-input','placeholder':'Sprint 1'}),
            'goal': forms.Textarea(attrs={'class':'cu-input','rows':2}),
            'status': forms.Select(attrs={'class':'cu-select'}),
            'start_date': forms.DateInput(attrs={'class':'cu-input','type':'date'}),
            'end_date': forms.DateInput(attrs={'class':'cu-input','type':'date'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['goal','start_date','end_date']: self.fields[f].required = False


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name','color']
        widgets = {
            'name': forms.TextInput(attrs={'class':'cu-input','placeholder':'Назва тегу'}),
            'color': forms.TextInput(attrs={'type':'color'}),
        }


class TaskFilterForm(forms.Form):
    status = forms.ChoiceField(choices=[('','Статус')]+Task.STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class':'cu-select-sm'}))
    priority = forms.ChoiceField(choices=[('','Пріоритет')]+Task.PRIORITY_CHOICES, required=False, widget=forms.Select(attrs={'class':'cu-select-sm'}))
    issue_type = forms.ChoiceField(choices=[('','Тип')]+Task.TYPE_CHOICES, required=False, widget=forms.Select(attrs={'class':'cu-select-sm'}))
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'cu-input-sm','placeholder':'Пошук...'}))


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class':'cu-input','placeholder':'Email (необов\'язково)'}))
    class Meta:
        model = User
        fields = ['username','email','password1','password2']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['username','password1','password2']:
            self.fields[f].widget.attrs['class'] = 'cu-input'
        self.fields['username'].widget.attrs['placeholder'] = 'Логін'
        self.fields['password1'].widget.attrs['placeholder'] = 'Пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторіть пароль'
        for f in ['username','password1','password2']: self.fields[f].help_text = None
        self.fields['username'].label = 'Логін'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Підтвердження'


from .models import Company, CompanyMembership


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'username', 'description', 'avatar_color', 'is_open']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'cu-input', 'placeholder': 'Назва компанії'}),
            'username': forms.TextInput(attrs={'class': 'cu-input', 'placeholder': 'company_handle'}),
            'description': forms.Textarea(attrs={'class': 'cu-input', 'rows': 3, 'placeholder': 'Про що ваша компанія...'}),
            'avatar_color': forms.TextInput(attrs={'type': 'color'}),
            'is_open': forms.CheckboxInput(attrs={'class': 'cu-checkbox'}),
        }

    def clean_username(self):
        u = self.cleaned_data['username'].strip().lower().replace(' ', '_')
        return u


class MembershipApplicationForm(forms.ModelForm):
    class Meta:
        model = CompanyMembership
        fields = ['display_name', 'tag', 'motivation']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'cu-input', 'placeholder': "Ваше ім'я у компанії"}),
            'tag': forms.TextInput(attrs={'class': 'cu-input', 'placeholder': 'Розробник / Дизайнер / Менеджер...'}),
            'motivation': forms.Textarea(attrs={'class': 'cu-input', 'rows': 4, 'placeholder': 'Опишіть чим хочете займатися...'}),
        }
        labels = {
            'display_name': "Ім'я у компанії",
            'tag': 'Ваша роль / тег',
            'motivation': 'Що хочу робити',
        }


class MembershipReviewForm(forms.Form):
    action = forms.ChoiceField(choices=[('approve', 'Прийняти'), ('reject', 'Відхилити')])
    reject_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'cu-input', 'rows': 2, 'placeholder': 'Причина відмови (необов\'язково)'}),
        label='Причина відмови'
    )
