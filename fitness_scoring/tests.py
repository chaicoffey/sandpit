from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.importlib import import_module
from fitness_scoring.models import School, Teacher

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

    def test_delete_school_safe_with_assigned_teachers(self):
        """
        delete_school_safe() should return False for schools who have teachers
        assigned to them.
        """
        testschool = School(name="Test School")
        testschool_teacher = Teacher(first_name='F1', surname='S1', school_id=testschool)
        self.assertEqual(testschool.delete_school_safe(), False)


class AdministratorViewTests(SessionTestCase):

    def test_administrator_view_without_authorisation(self):
        """
        Accessing the administrator view if you're not logged in should result
        in you being redirected to the login page.
        """
        # use follow=True to follow redirect (expect to be redirected to login page
        response = self.client.get(reverse('administrator'), follow=True)
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
        ##  Workaround: the admin view will fail if school does not exist.
        ##              Look into putting data creation elsewhere.
        testschool = School(name="Test School")
        testschool.save()
        session['school_name'] = "Test School"
        session.save()
        ##  Workaround end.
        response = self.client.get(reverse('administrator'))
        self.assertContains(response, "Teacher List")