from django.contrib import admin
from .models import Task, Tag, Project, Sprint, Comment

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'owner', 'is_public', 'created_at')
    filter_horizontal = ('members',)

@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'status', 'start_date', 'end_date')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'owner')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assignee', 'status', 'priority', 'is_open_task')
    list_filter = ('status', 'priority', 'issue_type', 'is_open_task')
    filter_horizontal = ('tags', 'mentioned_users')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')


from .models import Company, CompanyMembership

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'owner', 'is_open', 'created_at')
    search_fields = ('name', 'username')

@admin.register(CompanyMembership)
class CompanyMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'tag', 'status', 'created_at')
    list_filter = ('status', 'company')
    actions = ['approve', 'reject']

    def approve(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status='pending').update(
            status='approved', reviewed_by=request.user, reviewed_at=timezone.now()
        )
    approve.short_description = 'Прийняти вибрані заявки'

    def reject(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status='pending').update(
            status='rejected', reviewed_by=request.user, reviewed_at=timezone.now()
        )
    reject.short_description = 'Відхилити вибрані заявки'
