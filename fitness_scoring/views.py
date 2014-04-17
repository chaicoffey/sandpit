from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.template import RequestContext
from fitness_scoring.models import User, Teacher, Administrator, SuperUser, School, TestCategory, Test
from fitness_scoring.forms import AddSchoolForm, AddSchoolsForm, EditSchoolForm
from fitness_scoring.forms import AddTestCategoryForm, AddTestCategoriesForm, EditTestCategoryForm
from fitness_scoring.forms import AddTestForm, AddTestsForm, EditTestForm
from view_handlers import handle_teacher_list, handle_student_list, handle_class_list


def logout_user(request):
    request.session.flush()
    return redirect('fitness_scoring.views.login_user')


def login_user(request):

    def authenticate(username_local, password_local):

        def check_password(password_local2, encrypted_password):
            return password_local2 == encrypted_password

        users = User.objects.filter(username=username_local)
        if users.exists():
            superusers = SuperUser.objects.filter(user=users[0])
            administrators = Administrator.objects.filter(user=users[0])
            teachers = Teacher.objects.filter(user=users[0])
            if superusers.exists():
                if check_password(password_local2=password_local, encrypted_password=superusers[0].user.password):
                    user_type_local = 'SuperUser'
                else:
                    user_type_local = 'SuperUser Failed'
            elif administrators.exists():
                if check_password(password_local2=password_local, encrypted_password=administrators[0].user.password):
                    if administrators[0].school_id.subscription_paid:
                        user_type_local = 'Administrator'
                    else:
                        user_type_local = 'Unpaid'
                else:
                    user_type_local = 'Administrator Failed'
            elif teachers.exists():
                if check_password(password_local2=password_local, encrypted_password=teachers[0].user.password):
                    if teachers[0].school_id.subscription_paid:
                        user_type_local = 'Teacher'
                    else:
                        user_type_local = 'Unpaid'
                else:
                    user_type_local = 'Teacher Failed'

            else:
                user_type_local = 'Failed'
        else:
            user_type_local = 'Failed'

        return user_type_local

    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_type = authenticate(username_local=username, password_local=password)
        request.session['user_type'] = user_type   
        request.session['username'] = username
        if user_type == 'SuperUser':
            return redirect('fitness_scoring.views.superuser_view')
        elif user_type == 'Administrator':
            request.session['school_name'] = \
                Administrator.objects.get(user=User.objects.get(username=username)).school_id.name
            return redirect('fitness_scoring.views.administrator_view')
        elif user_type == 'Teacher':
            request.session['school_name'] = \
                Teacher.objects.get(user=User.objects.get(username=username)).school_id.name
            return redirect('fitness_scoring.views.teacher_view')
        elif user_type == 'Unpaid':
            state = "Subscription fee has not been paid for your school."
            return render(request, 'authentication.html', RequestContext(request, {'state': state,
                                                                                   'username': username}))
        else:
            state = "Incorrect username and/or password."
            return render(request, 'authentication.html', RequestContext(request, {'state': state,
                                                                                   'username': username}))
    else:
        return render(request, 'authentication.html', RequestContext(request, {'state': '', 'username': ''}))


def teacher_view(request):
    if request.session.get('user_type', None) == 'Teacher':

        last_active_tab1 = 'student_list'

        teacher = Teacher.objects.get(user=User.objects.get(username=request.session.get('username')))
        heading = teacher.first_name + ' ' + teacher.surname + ' (' + teacher.school_id.name + ')'
        context = {'logged_in_heading': heading,
                   'user_name': request.session.get('username'),
                   'submit_to_page': '/teacher/'}

        if handle_student_list(request, context, csv_available=False):
            last_active_tab1 = 'student_list'

        context['last_active_tab'] = last_active_tab1

        return render(request, 'teacher.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def administrator_view(request):
    if request.session.get('user_type', None) == 'Administrator':

        administrator = Administrator.objects.get(user=User.objects.get(username=request.session.get('username')))
        context = {'logged_in_heading': 'Administrator: ' + administrator.school_id.name,
                   'user_name': request.session.get('username'),
                   'submit_to_page': '/administrator/'}

        last_active_tab = 'teacher_list'

        if handle_teacher_list(request, context):
            last_active_tab = 'teacher_list'
        if handle_student_list(request, context):
            last_active_tab = 'student_list'
        if handle_class_list(request, context):
            last_active_tab = 'class_list'

        context['last_active_tab'] = last_active_tab

        return render(request, 'administrator.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def superuser_view(request):
    if request.session.get('user_type', None) == 'SuperUser':

        context = {
            'logged_in_heading': 'Super User Page',
            'user_name': request.session.get('username'),
            'user_tab_page_title': 'Super User',
            'user_tabs': [
                ['Home', '/superuser_home/', 'user_home_page'],
                ['Add/Update School List', '/school/list/', 'item_list:2'],
                ['Add/Update Test Category List', '/test_category/list/', 'item_list:2'],
                ['Add/Update Test List', '/test/list/', 'item_list:2']
            ]
        }

        return render(request, 'user_tab_page.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def superuser_home(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {'user_home_page_title': 'Super User',
                   'user_home_page_text': 'Select the view via the navigation side bar to the left'}
        return render(request, 'user_home_page.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def school_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(school, school.get_display_items()) for school in School.objects.all()],
            'item_list_title': 'School List',
            'item_list_table_headings': School.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['/school/add/', 'Add School'],
                       ['/school/adds/', 'Add/Edit Schools From .CSV']]]
            ],
            'item_list_options': [
                ['/school/edit/', 'pencil'],
                ['/school/delete/', 'remove']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view school list")


def school_add(request):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            school_add_form = AddSchoolForm(request.POST)
            if school_add_form.add_school():
                context = {'finish_title': 'School Added', 'user_message': 'School Added Successfully: '
                                                                           + school_add_form.cleaned_data['name']}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/school/add/', 'functionality_name': 'Add School', 'form': school_add_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/school/add/', 'functionality_name': 'Add School', 'form': AddSchoolForm()}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add a school")


def school_adds(request):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            school_adds_form = AddSchoolsForm(request.POST, request.FILES)
            result = school_adds_form.add_schools(request)
            if result:
                (n_created, n_updated, n_not_created_or_updated) = result
                result_message = ['Schools Created: '+str(n_created),
                                  'Schools Updated: '+str(n_updated),
                                  'No Changes From Data Lines: '+str(n_not_created_or_updated)]
                context = {'finish_title': 'Schools Added/Updated', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/school/adds/',
                           'functionality_name': 'Add Schools',
                           'form': school_adds_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/school/adds/', 'functionality_name': 'Add Schools', 'form': AddSchoolsForm()}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add schools")


def school_edit(request, school_pk):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            school_edit_form = EditSchoolForm(data=request.POST)
            if school_edit_form.edit_school():
                context = {'finish_title': 'School Edited',
                           'user_message': 'School Edited Successfully: ' + school_edit_form.cleaned_data['name']}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/school/edit/' + str(school_pk),
                           'functionality_name': 'Edit School',
                           'form': school_edit_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/school/edit/' + str(school_pk),
                       'functionality_name': 'Edit School',
                       'form': EditSchoolForm(school_pk=school_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to edit a school")


def school_delete(request, school_pk):
    if request.session.get('user_type', None) == 'SuperUser':
        school_to_delete = School.objects.get(pk=school_pk)
        school_name = school_to_delete.name
        if request.POST:
            if school_to_delete.delete_school_safe():
                context = {'finish_title': 'School Deleted',
                           'user_message': 'School Deleted Successfully: ' + school_name}
            else:
                context = {'finish_title': 'School Not Deleted',
                           'user_error_message': 'Could Not Delete ' + school_name + ' (School Being Used)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/school/delete/' + str(school_pk),
                       'functionality_name': 'Delete School',
                       'prompt_message': 'Are You Sure You Wish To Delete ' + school_name + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a school")


def test_category_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(test_category, test_category.get_display_items())
                          for test_category in TestCategory.objects.all()],
            'item_list_title': 'Test Category List',
            'item_list_table_headings': TestCategory.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['/test_category/add/', 'Add Test Category'],
                       ['/test_category/adds/', 'Add/Edit Test Categories From .CSV']]]
            ],
            'item_list_options': [
                ['/test_category/edit/', 'pencil'],
                ['/test_category/delete/', 'remove']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view test category list")


def test_category_add(request):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            test_category_add_form = AddTestCategoryForm(request.POST)
            if test_category_add_form.add_test_category():
                context = {'finish_title': 'Test Category Added',
                           'user_message': 'Test Category Added Successfully: '
                                           + test_category_add_form.cleaned_data['test_category_name']}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/test_category/add/',
                           'functionality_name': 'Add Test Category',
                           'form': test_category_add_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/test_category/add/',
                       'functionality_name': 'Add Test Category',
                       'form': AddTestCategoryForm()}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add a test category")


def test_category_adds(request):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            test_category_adds_form = AddTestCategoriesForm(request.POST, request.FILES)
            result = test_category_adds_form.add_test_categories(request)
            if result:
                (n_created, n_updated, n_not_created_or_updated) = result
                result_message = ['Test Categories Created: '+str(n_created),
                                  'Test Categories Updated: '+str(n_updated),
                                  'No Changes From Data Lines: '+str(n_not_created_or_updated)]
                context = {'finish_title': 'Test Categories Added/Updated', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/test_category/adds/',
                           'functionality_name': 'Add Test Categories',
                           'form': test_category_adds_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/test_category/adds/',
                       'functionality_name': 'Add Test Categories',
                       'form': AddTestCategoriesForm()}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add test categories")


def test_category_edit(request, test_category_pk):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            test_category_edit_form = EditTestCategoryForm(data=request.POST)
            if test_category_edit_form.edit_test_category():
                context = {'finish_title': 'Test Category Edited',
                           'user_message': 'Test Category Edited Successfully: '
                                           + test_category_edit_form.cleaned_data['test_category_name']}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/test_category/edit/' + str(test_category_pk),
                           'functionality_name': 'Edit Test Category',
                           'form': test_category_edit_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/test_category/edit/' + str(test_category_pk),
                       'functionality_name': 'Edit Test Category',
                       'form': EditTestCategoryForm(test_category_pk=test_category_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to edit a test category")


def test_category_delete(request, test_category_pk):
    if request.session.get('user_type', None) == 'SuperUser':
        test_category_to_delete = TestCategory.objects.get(pk=test_category_pk)
        test_category_name = test_category_to_delete.test_category_name
        if request.POST:
            if test_category_to_delete.delete_test_category_safe():
                context = {'finish_title': 'Test Category Deleted',
                           'user_message': 'Test Category Deleted Successfully: ' + test_category_name}
            else:
                context = {'finish_title': 'Test Category Not Deleted',
                           'user_error_message': 'Could Not Delete ' + test_category_name
                                                 + ' (Test Category Being Used)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/test_category/delete/' + str(test_category_pk),
                       'functionality_name': 'Delete Test Category',
                       'prompt_message': 'Are You Sure You Wish To Delete ' + test_category_name + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a test category")


def test_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(test, test.get_display_items())
                          for test in Test.objects.all()],
            'item_list_title': 'Test List',
            'item_list_table_headings': Test.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['/test/add/', 'Add Test'],
                       ['/test/adds/', 'Add/Edit Tests From .CSV']]]
            ],
            'item_list_options': [
                ['/test/edit/', 'pencil'],
                ['/test/delete/', 'remove']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view test list")


def test_add(request):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            test_add_form = AddTestForm(request.POST)
            if test_add_form.add_test():
                context = {'finish_title': 'Test Added',
                           'user_message': 'Test Added Successfully: '
                                           + test_add_form.cleaned_data['test_name']}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/test/add/',
                           'functionality_name': 'Add Test',
                           'form': test_add_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/test/add/',
                       'functionality_name': 'Add Test',
                       'form': AddTestForm()}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add a test")


def test_adds(request):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            test_adds_form = AddTestsForm(request.POST, request.FILES)
            result = test_adds_form.add_tests(request)
            if result:
                (n_created, n_updated, n_not_created_or_updated) = result
                result_message = ['Tests Created: '+str(n_created),
                                  'Tests Updated: '+str(n_updated),
                                  'No Changes From Data Lines: '+str(n_not_created_or_updated)]
                context = {'finish_title': 'Tests Added/Updated', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/test/adds/',
                           'functionality_name': 'Add Tests',
                           'form': test_adds_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/test/adds/',
                       'functionality_name': 'Add Tests',
                       'form': AddTestsForm()}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add tests")


def test_edit(request, test_pk):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            test_edit_form = EditTestForm(data=request.POST)
            if test_edit_form.edit_test():
                context = {'finish_title': 'Test Edited',
                           'user_message': 'Test Edited Successfully: '
                                           + test_edit_form.cleaned_data['test_name']}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/test/edit/' + str(test_pk),
                           'functionality_name': 'Edit Test',
                           'form': test_edit_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/test/edit/' + str(test_pk),
                       'functionality_name': 'Edit Test',
                       'form': EditTestForm(test_pk=test_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to edit a test")


def test_delete(request, test_pk):
    if request.session.get('user_type', None) == 'SuperUser':
        test_to_delete = Test.objects.get(pk=test_pk)
        test_name = test_to_delete.test_name
        if request.POST:
            if test_to_delete.delete_test_safe():
                context = {'finish_title': 'Test Deleted',
                           'user_message': 'Test Deleted Successfully: ' + test_name}
            else:
                context = {'finish_title': 'Test Not Deleted',
                           'user_error_message': 'Could Not Delete ' + test_name
                                                 + ' (Test Being Used)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/test/delete/' + str(test_pk),
                       'functionality_name': 'Delete Test',
                       'prompt_message': 'Are You Sure You Wish To Delete ' + test_name + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a test")