from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.importlib import import_module
from fitness_scoring.models import School, Teacher, Administrator, User

# Create your tests here.


class SessionTestCase(TestCase):
    """
    This class is being used to enable testing of sessions.  It should not be
    required as TestCase.Client.Session should allow save() functionality,
    but there is a long standing bug in django which means this is not working.
    """
    def setUp(self):
        # http://code.djangoproject.com/ticket/10899
        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.session = store
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key


class SchoolMethodTests(TestCase):

    def setUp(self):
        school = School.objects.create(name="Test School")
        adminuser = User.objects.create()
        User.objects.create(username='testuser', password='testpword')
        Administrator.objects.create(school_id=school, user=adminuser)

    def test_delete_school_safe_with_assigned_teachers(self):
        """
        delete_school_safe() should return False for schools who have teachers
        assigned to them.
        """
        testschool = School.objects.get(name="Test School")
        testuser = User.objects.get(username='testuser')
        Teacher.objects.create(first_name='F1', surname='S1', school_id=testschool, user=testuser)
        self.assertEqual(testschool.delete_school_safe(), False)


class AdministratorViewTests(SessionTestCase):

    def setUp(self):
        super(AdministratorViewTests, self).setUp()
        school = School.objects.create(name="Test School")
        adminuser = User.objects.create(username='adminuser', password='adminpword')
        Administrator.objects.create(school_id=school, user=adminuser)

    def test_administrator_view_without_authorisation(self):
        """
        Accessing the administrator view if you're not logged in should result
        in you being redirected to the login page.
        """
        # use follow=True to follow redirect (expect to be redirected to login page
        response = self.client.get(reverse('administrator_view'), follow=True)
        self.assertContains(response, "Please sign in")
        self.assertRedirects(response, 'login')

    def test_administrator_view_with_administrator_logged_in(self):
        """
        Accessing the administrator view when logged in as an administrator user
        should result in you being presented with the administrator page.
        """
        session = self.session
        session['user_type'] = 'Administrator'
        session.save()
        ##  Workaround: the admin view will fail if school or admin user does not exist.
        session['username'] = 'adminuser'
        session['school_name'] = "Test School"
        session.save()
        ##  Workaround end.
        response = self.client.get(reverse('administrator_view'))
        self.assertContains(response, "Administrator:")


class SchoolListViewTests(SessionTestCase):

    def setUp(self):
        super(SchoolListViewTests, self).setUp()
        school = School.objects.create(name="Test School")
        adminuser = User.objects.create(username='adminuser', password='adminpword')
        Administrator.objects.create(school_id=school, user=adminuser)

    def test_school_list_view_without_authorisation(self):
        """
        Accessing the school_list view if you're not logged in should result
        in a 403 response and the message 'You are not authorised to view school list'.
        """
        # use follow=True to follow redirect (expect to be redirected to login page
        response = self.client.get(reverse('school_list'), follow=True)
        self.assertContains(response, "You are not authorised to view school list", status_code=403)

    def test_school_list_view_with_superuser_logged_in(self):
        """
        Accessing the school_list view when logged in as a superuser
        should result in you being presented with the school_list page.
        The school_list view should display a list of schools in the
        system.  The attributes to be displayed include the school name,
        subscription status, and the name of the administrator.
        """
        session = self.session
        session['user_type'] = 'SuperUser'
        session.save()
        response = self.client.get(reverse('school_list'))
        self.assertContains(response, "School List")
        self.assertContains(response, "Test School")