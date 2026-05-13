from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('board/', views.PublicBoardView.as_view(), name='public_board'),
    path('board/take/<int:pk>/', views.TakeTaskView.as_view(), name='take_task'),

    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('projects/<int:project_pk>/sprints/create/', views.SprintCreateView.as_view(), name='sprint_create'),
    path('sprints/<int:pk>/', views.SprintDetailView.as_view(), name='sprint_detail'),

    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/kanban/', views.KanbanView.as_view(), name='kanban'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:pk>/status/', views.TaskUpdateStatusView.as_view(), name='task_status'),

    path('comments/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),

    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('tags/create/', views.TagCreateView.as_view(), name='tag_create'),
    path('tags/<int:pk>/delete/', views.TagDeleteView.as_view(), name='tag_delete'),

    path('api/users/', views.UserSearchView.as_view(), name='user_search'),
]

# Companies
from django.urls import path
urlpatterns += [
    path('companies/', views.CompanyCatalogView.as_view(), name='company_catalog'),
    path('companies/create/', views.CompanyCreateView.as_view(), name='company_create'),
    path('companies/<int:pk>/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('companies/<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='company_update'),
    path('companies/<int:pk>/apply/', views.CompanyApplyView.as_view(), name='company_apply'),
    path('companies/<int:pk>/leave/', views.MembershipLeaveView.as_view(), name='company_leave'),
    path('membership/<int:pk>/review/', views.MembershipReviewView.as_view(), name='membership_review'),
    path('membership/<int:pk>/kick/', views.MembershipKickView.as_view(), name='membership_kick'),
]
