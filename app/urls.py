from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.StudentLoginView.as_view(), name='login'),
    path('logout/', views.StudentLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('schedules/create/', views.schedule_create, name='schedule_create'),
    path(
        'schedules/<int:pk>/update/',
        views.schedule_update,
        name='schedule_update',
    ),
    path(
        'schedules/<int:pk>/delete/',
        views.schedule_delete,
        name='schedule_delete',
    ),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/update/', views.task_update, name='task_update'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
]
