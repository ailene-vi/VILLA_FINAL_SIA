from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ScheduleForm, StudentRegistrationForm, TaskForm
from .models import Schedule, Task


def _wants_json(request):
    """Return whether the caller requested an AJAX/JSON response."""
    return (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('accept', '')
    )


def _form_error_message(form):
    """Convert bound form errors into a concise flash message."""
    errors = []
    for field_errors in form.errors.values():
        errors.extend(str(error) for error in field_errors)
    return ' '.join(errors) or 'Please check the form and try again.'


class StudentLoginView(LoginView):
    """Sign a student in with Django's built-in authentication."""

    template_name = 'login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.POST.get('remember_me'):
            self.request.session.set_expiry(60 * 60 * 24 * 14)
        else:
            self.request.session.set_expiry(0)
        return response


class StudentLogoutView(LogoutView):
    """Sign a student out using Django's POST-only logout behavior."""

    next_page = 'login'


def register(request):
    """Create and sign in a new student account."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = StudentRegistrationForm(
        request.POST or None,
        initial={'username': ''},
    )
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        if request.POST.get('remember_me'):
            request.session.set_expiry(60 * 60 * 24 * 14)
        else:
            request.session.set_expiry(0)
        messages.success(request, 'Welcome! Your student account is ready.')
        return redirect('dashboard')
    return render(request, 'register.html', {'form': form})


@login_required
def dashboard(request):
    """Show the signed-in student's schedule and task overview."""
    today = timezone.localdate()
    now = timezone.now()
    week_end = now + timedelta(days=7)
    schedules = Schedule.objects.filter(owner=request.user)
    tasks = Task.objects.filter(owner=request.user)

    context = {
        'today': today,
        'weekdays': [
            {'name': name, 'short': short}
            for name, short in (
                ('Monday', 'Mon'),
                ('Tuesday', 'Tue'),
                ('Wednesday', 'Wed'),
                ('Thursday', 'Thu'),
                ('Friday', 'Fri'),
                ('Saturday', 'Sat'),
                ('Sunday', 'Sun'),
            )
        ],
        'timetable_hours': [
            {
                'hour': hour,
                'label': (
                    f'{hour % 12 or 12} '
                    f'{"AM" if hour < 12 else "PM"}'
                ),
            }
            for hour in range(8, 18)
        ],
        'today_schedules': schedules.filter(
            day=today.strftime('%A')
        ).order_by('start_time'),
        'schedules': schedules,
        'tasks': tasks,
        'pending_count': tasks.filter(status='Pending').count(),
        'completed_count': tasks.filter(status='Completed').count(),
        'due_this_week_count': tasks.filter(
            deadline__gte=now,
            deadline__lte=week_end,
        ).exclude(status='Completed').count(),
        'due_soon_tasks': tasks.filter(
            deadline__gte=now,
            deadline__lte=week_end,
        ).exclude(status='Completed'),
        'schedule_form': ScheduleForm(),
        'task_form': TaskForm(),
        'task_types': Task.TASK_TYPE_CHOICES,
    }
    return render(request, 'dashboard.html', context)


@login_required
@require_POST
def schedule_create(request):
    """Create a class meeting owned by the signed-in student."""
    form = ScheduleForm(request.POST)
    if form.is_valid():
        schedule = form.save(commit=False)
        schedule.owner = request.user
        schedule.save()
        messages.success(request, 'Class added to your schedule.')
        if _wants_json(request):
            return JsonResponse(
                {'ok': True, 'message': 'Class added to your schedule.'},
                status=201,
            )
        return redirect('dashboard')

    error = _form_error_message(form)
    messages.error(request, error)
    if _wants_json(request):
        return JsonResponse(
            {'ok': False, 'message': error, 'errors': form.errors},
            status=400,
        )
    return redirect('dashboard')


@login_required
@require_POST
def schedule_update(request, pk):
    """Update one of the signed-in student's class meetings."""
    schedule = get_object_or_404(Schedule, pk=pk, owner=request.user)
    form = ScheduleForm(request.POST, instance=schedule)
    if form.is_valid():
        form.save()
        messages.success(request, 'Class details updated.')
        if _wants_json(request):
            return JsonResponse(
                {'ok': True, 'message': 'Class details updated.'}
            )
        return redirect('dashboard')

    error = _form_error_message(form)
    messages.error(request, error)
    if _wants_json(request):
        return JsonResponse(
            {'ok': False, 'message': error, 'errors': form.errors},
            status=400,
        )
    return redirect('dashboard')


@login_required
@require_POST
def schedule_delete(request, pk):
    """Delete one of the signed-in student's class meetings."""
    schedule = get_object_or_404(Schedule, pk=pk, owner=request.user)
    schedule.delete()
    messages.success(request, 'Class removed from your schedule.')
    if _wants_json(request):
        return JsonResponse(
            {'ok': True, 'message': 'Class removed from your schedule.'}
        )
    return redirect('dashboard')


@login_required
@require_POST
def task_create(request):
    """Create a task owned by the signed-in student."""
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.owner = request.user
        task.save()
        messages.success(request, 'Task added to your list.')
        if _wants_json(request):
            return JsonResponse(
                {'ok': True, 'message': 'Task added to your list.'},
                status=201,
            )
        return redirect('dashboard')

    error = _form_error_message(form)
    messages.error(request, error)
    if _wants_json(request):
        return JsonResponse(
            {'ok': False, 'message': error, 'errors': form.errors},
            status=400,
        )
    return redirect('dashboard')


@login_required
@require_POST
def task_update(request, pk):
    """Update one of the signed-in student's tasks."""
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    form = TaskForm(request.POST, instance=task)
    if form.is_valid():
        form.save()
        messages.success(request, 'Task updated.')
        if _wants_json(request):
            return JsonResponse({'ok': True, 'message': 'Task updated.'})
        return redirect('dashboard')

    error = _form_error_message(form)
    messages.error(request, error)
    if _wants_json(request):
        return JsonResponse(
            {'ok': False, 'message': error, 'errors': form.errors},
            status=400,
        )
    return redirect('dashboard')


@login_required
@require_POST
def task_delete(request, pk):
    """Delete one of the signed-in student's tasks."""
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    task.delete()
    messages.success(request, 'Task deleted.')
    if _wants_json(request):
        return JsonResponse({'ok': True, 'message': 'Task deleted.'})
    return redirect('dashboard')
