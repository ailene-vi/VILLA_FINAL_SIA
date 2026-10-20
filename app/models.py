from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Schedule(models.Model):
    """A recurring class meeting owned by a student."""

    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    subject_name = models.CharField(max_length=200)
    subject_code = models.CharField(max_length=50)
    instructor = models.CharField(max_length=200)
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='schedule_owned',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day', 'start_time']

    def clean(self):
        """Ensure a class ends after it starts."""
        super().clean()
        if (
            self.start_time
            and self.end_time
            and self.end_time <= self.start_time
        ):
            raise ValidationError(
                {'end_time': 'End time must be later than start time.'}
            )

    @property
    def duration_slots(self):
        """Return the class length rounded up to whole timetable hours."""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return max(1, (end_minutes - start_minutes + 59) // 60)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.subject_name} ({self.subject_code})'


class Task(models.Model):
    """A school activity or deadline owned by a student."""

    TASK_TYPE_CHOICES = [
        ('Activity', 'Activity'),
        ('Project', 'Project'),
        ('Assignment', 'Assignment'),
        ('Exam', 'Exam'),
        ('Deadline', 'Deadline'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    task_name = models.CharField(max_length=200)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    subject = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    deadline = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='Medium',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_owned',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deadline', 'task_name']

    def clean(self):
        """Reject a past deadline on a newly created task."""
        super().clean()
        if (
            self.pk is None
            and self.deadline
            and self.deadline < timezone.now()
        ):
            raise ValidationError(
                {'deadline': 'A new task deadline cannot be in the past.'}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.task_name} ({self.task_type})'
