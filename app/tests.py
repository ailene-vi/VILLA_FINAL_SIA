from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Schedule, Task


class StudentCalendarTests(TestCase):
    """Verify student authentication, ownership, and calendar workflows."""

    def setUp(self):
        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='A-reliable-password-2026',
        )
        self.other_student = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='A-reliable-password-2026',
        )
        self.client.force_login(self.student)

    def test_dashboard_requires_login(self):
        """Anonymous users are sent to the sign-in page."""
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("dashboard")}',
        )

    def test_dashboard_only_shows_owned_records(self):
        """The dashboard never includes another student's records."""
        Schedule.objects.create(
            subject_name='My class',
            subject_code='MTH101',
            instructor='A. Teacher',
            day='Monday',
            start_time='09:00',
            end_time='10:00',
            room='A1',
            owner=self.student,
        )
        Schedule.objects.create(
            subject_name='Private class',
            subject_code='BIO101',
            instructor='B. Teacher',
            day='Monday',
            start_time='10:00',
            end_time='11:00',
            room='B1',
            owner=self.other_student,
        )
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'My class')
        self.assertNotContains(response, 'Private class')

    def test_schedule_create_assigns_owner_and_validates_time(self):
        """Class creation assigns the current owner and rejects bad times."""
        response = self.client.post(
            reverse('schedule_create'),
            {
                'subject_name': 'Physics',
                'subject_code': 'PHY101',
                'instructor': 'Dr. Example',
                'day': 'Tuesday',
                'start_time': '09:00',
                'end_time': '10:00',
                'room': 'Lab 2',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 201)
        schedule = Schedule.objects.get(subject_code='PHY101')
        self.assertEqual(schedule.owner, self.student)

        invalid_response = self.client.post(
            reverse('schedule_create'),
            {
                'subject_name': 'Bad class',
                'subject_code': 'BAD101',
                'instructor': 'Dr. Example',
                'day': 'Tuesday',
                'start_time': '10:00',
                'end_time': '10:00',
                'room': 'Lab 2',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(invalid_response.status_code, 400)
        self.assertFalse(
            Schedule.objects.filter(subject_code='BAD101').exists()
        )

    def test_schedule_update_and_delete_are_owner_scoped(self):
        """A student cannot change or remove another student's class."""
        schedule = Schedule.objects.create(
            subject_name='Other class',
            subject_code='OTH101',
            instructor='Other teacher',
            day='Wednesday',
            start_time='09:00',
            end_time='10:00',
            room='Room 3',
            owner=self.other_student,
        )
        update = self.client.post(
            reverse('schedule_update', args=[schedule.pk]),
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        delete = self.client.post(
            reverse('schedule_delete', args=[schedule.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(update.status_code, 404)
        self.assertEqual(delete.status_code, 404)
        self.assertTrue(Schedule.objects.filter(pk=schedule.pk).exists())

    def test_task_create_and_status_update(self):
        """Tasks are owned and can be marked complete."""
        deadline = timezone.localtime(
            timezone.now() + timedelta(days=2)
        ).strftime('%Y-%m-%dT%H:%M')
        create = self.client.post(
            reverse('task_create'),
            {
                'task_name': 'Read chapter 4',
                'task_type': 'Assignment',
                'subject': 'History',
                'description': '',
                'deadline': deadline,
                'status': 'Pending',
                'priority': 'Medium',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(create.status_code, 201, create.content)
        task = Task.objects.get(task_name='Read chapter 4')
        self.assertEqual(task.owner, self.student)

        update = self.client.post(
            reverse('task_update', args=[task.pk]),
            {
                'task_name': task.task_name,
                'task_type': task.task_type,
                'subject': task.subject,
                'description': task.description,
                'deadline': deadline,
                'status': 'Completed',
                'priority': task.priority,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(update.status_code, 200, update.content)
        task.refresh_from_db()
        self.assertEqual(task.status, 'Completed')

    def test_new_task_cannot_have_a_past_deadline(self):
        """A past deadline is rejected when creating a task."""
        response = self.client.post(
            reverse('task_create'),
            {
                'task_name': 'Late task',
                'task_type': 'Deadline',
                'subject': '',
                'description': '',
                'deadline': '2020-01-01T09:00',
                'status': 'Pending',
                'priority': 'High',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Task.objects.filter(task_name='Late task').exists())

    def test_register_and_post_only_logout(self):
        """Registration uses Django auth and logout cannot be triggered by GET."""
        self.client.logout()
        register = self.client.post(
            reverse('register'),
            {
                'username': 'newstudent',
                'email': 'newstudent@example.com',
                'password1': 'A-new-strong-password-2026',
                'password2': 'A-new-strong-password-2026',
            },
        )
        self.assertRedirects(register, reverse('dashboard'))
        self.assertTrue(
            User.objects.filter(username='newstudent').exists()
        )
        self.assertEqual(
            self.client.get(reverse('logout')).status_code,
            405,
        )
