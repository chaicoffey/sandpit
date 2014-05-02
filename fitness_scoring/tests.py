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


class SchoolAddViewTests(SessionTestCase):

    def setUp(self):
        super(SchoolAddViewTests, self).setUp()
        school = School.objects.create(name="Test School")
        adminuser = User.objects.create(username='adminuser', password='adminpword')
        Administrator.objects.create(school_id=school, user=adminuser)

    def test_school_add_view_without_authorisation(self):
        """
        Accessing the school_add view if you're not logged in should result
        in a 403 response and the message 'You are not authorised to add a school'.
        """
        # use follow=True to follow redirect (expect to be redirected to login page
        response = self.client.get(reverse('school_add'), follow=True)
        self.assertContains(response, "You are not authorised to add a school", status_code=403)

    def test_school_add_view_with_superuser_logged_in(self):
        """
        Accessing the school_add view when logged in as a superuser
        should result in you being presented with the add school form.
        The form should allow you to enter a school name and the subscription paid status.
        """
        session = self.session
        session['user_type'] = 'SuperUser'
        session.save()
        response = self.client.get(reverse('school_add'))
        self.assertContains(response, "Add School")
        self.assertContains(response, "Name")
        self.assertContains(response, "Subscription paid")

    def test_school_add_post_with_existing_school_name(self):
        """
        Trying to add a school with the same name as an existing school should result in
        the school_add form being redisplayed along with an error message stating
        that 'School Already Exists'.
        """
        session = self.session
        session['user_type'] = 'SuperUser'
        session.save()
        response = self.client.post(reverse('school_add'), {'name': "Test School"})
        self.assertContains(response, "School Already Exists")

    def test_school_add_post_with_blank_school_name(self):
        """
        Trying to add a school without specifying a school name should result in
        the school_add form being redisplayed along with an error message stating
        that 'Please Enter School Name'.
        """
        session = self.session
        session['user_type'] = 'SuperUser'
        session.save()
        response = self.client.post(reverse('school_add'), {'name': ""})
        self.assertContains(response, "Please Enter School Name")

    def test_school_add_with_valid_data(self):
        """
        Trying to add a school with a unique and valid name should result in the
        school being created and the user receiving a success message stating
        that 'School Added Successfully'.
        """
        session = self.session
        session['user_type'] = 'SuperUser'
        session.save()
        response = self.client.post(reverse('school_add'), {'name': "New School"})
        self.assertContains(response, "School Added Successfully")
        response = self.client.post(reverse('school_add'), {'name': "New School2"})
        self.assertContains(response, "School Added Successfully")
        response = self.client.get(reverse('school_list'))
        self.assertEqual(len(response.context['item_list']), 3)


class SchoolDeleteViewTests(SessionTestCase):

    def setUp(self):
        super(SchoolDeleteViewTests, self).setUp()
        school = School.objects.create(name="Test School")
        adminuser = User.objects.create(username='adminuser', password='adminpword')
        Administrator.objects.create(school_id=school, user=adminuser)

    def test_school_delete_view_without_authorisation(self):
        """
        Accessing the school_delete view if you're not logged in should result
        in a 403 response and the message 'You are not authorised to delete a school'.
        """
        response = self.client.get(reverse('school_delete', kwargs={'school_pk': 1}), follow=True)
        self.assertContains(response, "You are not authorised to delete a school", status_code=403)

    def test_school_delete_view_with_superuser_logged_in(self):
        """
        Accessing the school_delete view (for a valid school_pk) when logged in as a superuser
        should result in you being presented with the delete school confirmation form.
        """
        session = self.session
        session['user_type'] = 'SuperUser'
        session.save()
        response = self.client.get(reverse('school_delete', kwargs={'school_pk': 1}))
        self.assertContains(response, "Delete School")
        self.assertContains(response, "Are You Sure You Wish To Delete")

    def test_school_delete_post_with_invalid_school_pk(self):
        """
        Trying to delete a school without using a valid school_pk should result in
        some sort of error message being displayed
        """
        pass

    def test_school_delete_with_valid_data(self):
        """
        Trying to delete a school using a valid school_pk should result in the
        school being deleted and the user receiving a success message stating
        that 'School Deleted Successfully'.
        """
        session = self.session
        session['user_type'] = 'SuperUser'
        session.save()
        response = self.client.get(reverse('school_list'))
        self.assertEqual(len(response.context['item_list']), 1)
        response = self.client.post(reverse('school_delete', kwargs={'school_pk': 1}), data={'': ''})
        # Need to have some data in the above post otherwise it seems to revert to a get request
        #print response.content
        self.assertContains(response, "School Deleted Successfully")
        response = self.client.get(reverse('school_list'))
        self.assertEqual(len(response.context['item_list']), 0)