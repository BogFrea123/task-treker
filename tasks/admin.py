from django.contrib import admin
from .models import Task, Tag

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'owner')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'priority', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'owner')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags',)
