from django.contrib import admin

from .models import Schedule, Task


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'subject_code', 'instructor', 'day', 'start_time', 'end_time', 'room')
    search_fields = ('subject_name', 'subject_code', 'instructor', 'room')
    list_filter = ('day', 'instructor')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'task_type', 'subject', 'deadline')
    search_fields = ('task_name', 'subject', 'description')
    list_filter = ('task_type', 'deadline')
