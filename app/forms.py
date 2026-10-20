from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Schedule, Task


class ScheduleForm(forms.ModelForm):
    """Validate and render a student's class meeting."""

    class Meta:
        model = Schedule
        fields = (
            'subject_name',
            'subject_code',
            'instructor',
            'day',
            'start_time',
            'end_time',
            'room',
        )
        widgets = {
            'subject_name': forms.TextInput(
                attrs={'class': 'form-control', 'autocomplete': 'off'}
            ),
            'subject_code': forms.TextInput(
                attrs={'class': 'form-control', 'autocomplete': 'off'}
            ),
            'instructor': forms.TextInput(
                attrs={'class': 'form-control', 'autocomplete': 'name'}
            ),
            'day': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(
                attrs={'class': 'form-control', 'type': 'time'}
            ),
            'end_time': forms.TimeInput(
                attrs={'class': 'form-control', 'type': 'time'}
            ),
            'room': forms.TextInput(
                attrs={'class': 'form-control', 'autocomplete': 'off'}
            ),
        }


class TaskForm(forms.ModelForm):
    """Validate and render a student's activity or deadline."""

    deadline = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S%z'],
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M',
        ),
    )

    class Meta:
        model = Task
        fields = (
            'task_name',
            'task_type',
            'subject',
            'description',
            'deadline',
            'status',
            'priority',
        )
        widgets = {
            'task_name': forms.TextInput(
                attrs={'class': 'form-control', 'autocomplete': 'off'}
            ),
            'task_type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(
                attrs={'class': 'form-control', 'autocomplete': 'off'}
            ),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }


class StudentRegistrationForm(UserCreationForm):
    """Create a new Django user with an email address."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'autocomplete': 'email',
                'placeholder': 'you@example.com',
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')
