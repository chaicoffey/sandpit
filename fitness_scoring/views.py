from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.template import RequestContext
from fitness_scoring.models import User, Teacher, Administrator, SuperUser, School, TestCategory, Test, Student, Class
from fitness_scoring.models import PercentileBracketList
from fitness_scoring.models import TeacherClassAllocation, ClassTest, StudentClassEnrolment, TestSet
from fitness_scoring.forms import AddSchoolForm, AddSchoolsForm, EditSchoolForm
from fitness_scoring.forms import AddTestCategoryForm, AddTestCategoriesForm, EditTestCategoryForm
from fitness_scoring.forms import AddTestsForm, EditTestForm, UpdateTestFromFileForm
from fitness_scoring.forms import AddTeacherForm, EditTeacherForm
from fitness_scoring.forms import AddClassForm, AddClassesForm, EditClassForm
from fitness_scoring.forms import AssignTestToClassForm, SaveClassTestsAsTestSetForm, LoadClassTestsFromTestSetForm
from pe_site.settings import DEFAULT_FROM_EMAIL
from django.core.mail import send_mail


def logout_user(request):
    request.session.flush()
    return redirect('fitness_scoring.views.login_user')


def login_user(request):

    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = User.get_authenticated_user(username=username, password=password)
        if user:
            if SuperUser.objects.filter(user=user).exists():
                user_type = 'SuperUser'
            elif Administrator.objects.filter(user=user).exists():
                if Administrator.objects.get(user=user).school_id.subscription_paid:
                    user_type = 'Administrator'
                else:
                    user_type = 'Unpaid'
            elif Teacher.objects.filter(user=user).exists():
                if Teacher.objects.get(user=user).school_id.subscription_paid:
                    user_type = 'Teacher'
                else:
                    user_type = 'Unpaid'
            elif Class.objects.filter(user=user).exists():
                if Class.objects.get(user=user).school_id.subscription_paid:
                    user_type = 'Class'
                else:
                    user_type = 'Unpaid'
            else:
                user_type = "Unrecognised User Type"
        else:
            user_type = "Authentication Failed"

        request.session['user_type'] = user_type   
        request.session['username'] = username

        if user_type == 'SuperUser':
            return redirect('fitness_scoring.views.superuser_view')
        elif user_type == 'Administrator':
            return redirect('fitness_scoring.views.administrator_view')
        elif user_type == 'Teacher':
            return redirect('fitness_scoring.views.teacher_view')
        elif user_type == 'Class':
            return redirect('fitness_scoring.views.class_student_view')
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


def class_student_view(request):
    if request.session.get('user_type', None) == 'Class':
        return render(request, 'student_entry_form.html', RequestContext(request, {}))
    else:
        return redirect('fitness_scoring.views.login_user')


def teacher_view(request):
    if request.session.get('user_type', None) == 'Teacher':

        teacher = Teacher.objects.get(user=User.objects.get(username=request.session.get('username')))
        heading = teacher.first_name + ' ' + teacher.surname + ' (' + teacher.school_id.name + ')'
        context = {
            'logged_in_heading': heading,
            'user_name': request.session.get('username'),
            'user_tab_page_title': heading,
            'user_tabs': [
                ['Home', '/teacher_home/', 'user_home_page']
            ]
        }

        return render(request, 'user_tab_page.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def teacher_home(request):
    if request.session.get('user_type', None) == 'Teacher':

        teacher = Teacher.objects.get(user=User.objects.get(username=request.session.get('username')))

        steps = [('Add Classes For Year', 'teacher_add_classes'),
                 ('Add Tests To Classes For The Year', 'teacher_add_tests'),
                 ('Run Tests (*temp* see my sheet for what instructions should contain *temp*)', 'teacher_run_tests'),
                 ('Get Students To Enter Results', 'teacher_student_enter_results'),
                 ('Approve Entries For Class', 'teacher_approve_entries'),
                 ('View Results', 'teacher_view_results')]
        non_optional_steps = 6
        steps_formatted = []
        for step_index in range(non_optional_steps):
            (step_text, instructions_name) = steps[step_index]
            steps_formatted.append(('Step ' + str(step_index + 1) + ': ' + step_text,
                                    '/instructions_page/' + instructions_name))

        heading = teacher.first_name + ' ' + teacher.surname + ' (' + teacher.school_id.name + ')'
        context = {'user_home_page_title': heading,
                   'steps': steps_formatted}
        return render(request, 'user_home_page.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def administrator_view(request):
    if request.session.get('user_type', None) == 'Administrator':

        administrator = Administrator.objects.get(user=User.objects.get(username=request.session.get('username')))
        context = {
            'logged_in_heading': 'Administrator: ' + administrator.school_id.name,
            'user_name': request.session.get('username'),
            'user_tab_page_title': 'Administrator: ' + administrator.school_id.name,
            'user_tabs': [
                ['Home', '/administrator_home/', 'user_home_page'],
                ['Add/Update Teacher List', '/teacher/list/', 'item_list:2'],
                ['Add/Update Class List', '/class/list/', 'item_list:2']
            ]
        }

        return render(request, 'user_tab_page.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def administrator_home(request):
    if request.session.get('user_type', None) == 'Administrator':

        administrator = Administrator.objects.get(user=User.objects.get(username=request.session.get('username')))

        steps = [('Add Teachers', 'administrator_add_teacher'),
                 ('Add Classes For Teachers For The Year', 'administrator_add_classes'),
                 ('Add Tests To Classes For The Year', 'administrator_add_tests')]
        non_optional_steps = 1
        steps_formatted = []
        for step_index in range(non_optional_steps):
            (step_text, instructions_name) = steps[step_index]
            steps_formatted.append(('Step ' + str(step_index + 1) + ': ' + step_text,
                                    '/instructions_page/' + instructions_name))
        steps_optional_formatted = []
        for step_index in range(non_optional_steps, len(steps)):
            (step_text, instructions_name) = steps[step_index]
            steps_optional_formatted.append(('Step ' + str(step_index + 1) + ': ' + step_text,
                                             '/instructions_page/' + instructions_name))

        context = {'user_home_page_title': 'Administrator: ' + administrator.school_id.name,
                   'steps': steps_formatted,
                   'steps_optional': steps_optional_formatted}
        return render(request, 'user_home_page.html', RequestContext(request, context))
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
                ['Add/Update Test List', '/test/list/', 'item_list:2'],
                ['Add/Update Test Category List', '/test_category/list/', 'item_list:2']
            ]
        }

        return render(request, 'user_tab_page.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def superuser_home(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {'user_home_page_title': 'Super User'}
        return render(request, 'user_home_page.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def instructions_page(request, instructions_name):
    user_type = request.session.get('user_type', None)
    if (instructions_name == 'administrator_add_teacher') and user_type == 'Administrator':
        return render(request, 'instructions/no_instructions.html', RequestContext(request, {}))
    elif instructions_name == 'administrator_add_classes' and user_type == 'Administrator':
        return render(request, 'instructions/no_instructions.html', RequestContext(request, {}))
    elif instructions_name == 'administrator_add_tests' and user_type == 'Administrator':
        return render(request, 'instructions/no_instructions.html', RequestContext(request, {}))
    elif instructions_name == 'teacher_add_classes' and user_type == 'Teacher':
        return render(request, 'instructions/no_instructions.html', RequestContext(request, {}))
    elif instructions_name == 'teacher_add_tests' and user_type == 'Teacher':
        return render(request, 'instructions/no_instructions.html', RequestContext(request, {}))
    elif instructions_name == 'teacher_run_tests' and user_type == 'Teacher':
        return render(request, 'instructions/no_instructions.html', RequestContext(request, {}))
    elif instructions_name == 'teacher_student_enter_results' and user_type == 'Teacher':
        return render(request, 'instructions/no_instructions.html', RequestContext(request, {}))
    elif instructions_name == 'teacher_approve_entries' and user_type == 'Teacher':
        return render(request, 'instructions/no_instructions.html', RequestContext(request, {}))
    elif instructions_name == 'teacher_view_results' and user_type == 'Teacher':
        return render(request, 'instructions/no_instructions.html', RequestContext(request, {}))
    else:
        return render(request, 'instructions/no_instructions.html', RequestContext(request, {}))


def school_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(school, school.get_display_items()) for school in School.objects.all()],
            'item_list_title': 'School List',
            'item_list_table_headings': School.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['modal_load_link', '/school/add/', 'Add School'],
                       ['modal_load_link', '/school/adds/', 'Add/Edit Schools From .CSV']]]
            ],
            'item_list_options': [
                ['modal_load_link', '/school/edit/', 'pencil'],
                ['modal_load_link', '/school/reset_password/', 'repeat'],
                ['modal_load_link', '/school/delete/', 'remove']
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
            school_edit_form = EditSchoolForm(school_pk=school_pk, data=request.POST)
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


def school_reset_password(request, school_pk):
    if request.session.get('user_type', None) == 'SuperUser':
        administrator = Administrator.objects.get(school_id=School.objects.get(pk=school_pk))
        if request.POST:
            new_password = administrator.reset_password()
            message = ('username: ' + administrator.user.username + '\n' +
                       'password: ' + new_password)
            send_mail('Fitness Testing App - Administrator Password Reset', message, DEFAULT_FROM_EMAIL,
                      [administrator.email])
            context = {'finish_title': 'Password Reset',
                       'user_message': 'Password Reset For User: ' + str(administrator)}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/school/reset_password/' + str(school_pk),
                       'functionality_name': 'Reset Password',
                       'prompt_message': 'Are You Sure You Wish To Reset The Password For ' + str(administrator) + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to reset the administrator password for a school")


def test_category_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(test_category, test_category.get_display_items())
                          for test_category in TestCategory.objects.all()],
            'item_list_title': 'Test Category List',
            'item_list_table_headings': TestCategory.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['modal_load_link', '/test_category/add/', 'Add Test Category'],
                       ['modal_load_link', '/test_category/adds/', 'Add/Edit Test Categories From .CSV']]]
            ],
            'item_list_options': [
                ['modal_load_link', '/test_category/edit/', 'pencil'],
                ['modal_load_link', '/test_category/delete/', 'remove']
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
            test_category_edit_form = EditTestCategoryForm(test_category_pk=test_category_pk, data=request.POST)
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
                ['+', [['modal_load_link', '/test/adds/', 'Add Tests From .CSVs']]]
            ],
            'item_list_options': [
                ['modal_load_link', '/test/edit/', 'pencil'],
                ['modal_load_link', '/test/update/', 'pencil'],
                ['percentile_load_link', '/test/percentile_brackets_graphs/None/', 'stats'],
                ['modal_load_link', '/test/delete/', 'remove']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view test list")


def test_adds(request):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            test_adds_form = AddTestsForm(data=request.POST, files=request.FILES)
            result = test_adds_form.add_tests(request)
            if result:
                (n_created, n_not_created) = result
                result_message = ['Tests Created: '+str(n_created),
                                  'No Changes From Data Lines: '+str(n_not_created)]
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
            test_edit_form = EditTestForm(test_pk=test_pk, data=request.POST)
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


def test_update(request, test_pk):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            test_update_form = UpdateTestFromFileForm(test_pk=test_pk, data=request.POST, files=request.FILES)
            if test_update_form.update_test(request):
                context = {'finish_title': 'Test Updated',
                           'user_message': 'Test Updated Successfully'}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'finish_title': 'Test Not Updated',
                           'user_message': 'Test Not Updated (Different Test Name Or Error in File)'}
                return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/test/update/' + str(test_pk),
                       'functionality_name': 'Update Test',
                       'form': UpdateTestFromFileForm(test_pk=test_pk)}
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


def test_percentile_brackets_graphs(request, percentile_bracket_list_pk, test_pk):
    if request.session.get('user_type', None) == 'SuperUser':
        test = Test.objects.get(pk=test_pk)
        percentile_bracket_lists = PercentileBracketList.objects.filter(percentile_bracket_set=test.percentiles)
        pk_local = (percentile_bracket_lists[0].pk
                    if (percentile_bracket_list_pk == 'None') and percentile_bracket_lists.exists()
                    else int(percentile_bracket_list_pk))
        context = {'test_label': str(test),
                   'age_gender_options': [('/test/percentile_brackets_graphs/' + str(bracket.pk) + '/' + str(test_pk),
                                           '(' + str(bracket.age) + ', ' + bracket.gender + ')',
                                           bracket.pk == pk_local) for bracket in percentile_bracket_lists],
                   'percentile_bracket_scores': PercentileBracketList.objects.get(pk=pk_local).get_scores(True)}
        return render(request, 'percentile_brackets_graph.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view the percentile brackets for a test")


def test_instructions(request, test_name):
    user_type = request.session.get('user_type', None)
    if (user_type == 'Administrator') or (user_type == 'Teacher'):
        if test_name == 'Jump 20m':
            return render(request, 'test_instructions/no_test_instructions.html', RequestContext(request, {}))
        elif test_name == 'Run 20m':
            return render(request, 'test_instructions/no_test_instructions.html', RequestContext(request, {}))
        elif test_name == 'Throw 20m':
            return render(request, 'test_instructions/no_test_instructions.html', RequestContext(request, {}))
        else:
            return render(request, 'test_instructions/no_test_instructions.html', RequestContext(request, {}))
    else:
        return HttpResponseForbidden("You are not authorised to view instructions for a test")


def teacher_list(request):
    if request.session.get('user_type', None) == 'Administrator':
        username = request.session.get('username', None)
        school = Administrator.objects.get(user=User.objects.get(username=username)).school_id
        context = {
            'item_list': [(teacher, teacher.get_display_items())
                          for teacher in Teacher.objects.filter(school_id=school)],
            'item_list_title': 'Teacher List',
            'item_list_table_headings': Teacher.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['modal_load_link', '/teacher/add/', 'Add Teacher']]]
            ],
            'item_list_options': [
                ['modal_load_link', '/teacher/edit/', 'pencil'],
                ['modal_load_link', '/teacher/reset_password/', 'repeat'],
                ['modal_load_link', '/teacher/delete/', 'remove']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view teacher list")


def teacher_add(request):
    if request.session.get('user_type', None) == 'Administrator':
        user = User.objects.get(username=request.session.get('username', None))
        school_pk = Administrator.objects.get(user=user).school_id.pk
        if request.POST:
            teacher_add_form = AddTeacherForm(school_pk=school_pk, data=request.POST)
            teacher = teacher_add_form.add_teacher()
            if teacher:
                context = {'finish_title': 'Teacher Added',
                           'user_message': 'Teacher Added Successfully: ' + str(teacher)}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/teacher/add/',
                           'functionality_name': 'Add Teacher',
                           'form': teacher_add_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/teacher/add/',
                       'functionality_name': 'Add Teacher',
                       'form': AddTeacherForm(school_pk=school_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add a teacher")


def teacher_edit(request, teacher_pk):
    authorised = request.session.get('user_type', None) == 'Administrator'
    if authorised:
        administrator = Administrator.objects.get(user=User.objects.get(username=request.session.get('username', None)))
        teacher = Teacher.objects.get(pk=teacher_pk)
        authorised = administrator.school_id == teacher.school_id

    if authorised:
        user = User.objects.get(username=request.session.get('username', None))
        school_pk = Administrator.objects.get(user=user).school_id.pk
        if request.POST:
            teacher_edit_form = EditTeacherForm(school_pk=school_pk, teacher_pk=teacher_pk, data=request.POST)
            teacher = teacher_edit_form.edit_teacher()
            if teacher:
                context = {'finish_title': 'Teacher Edited',
                           'user_message': 'Teacher Edited Successfully: ' + str(teacher)}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/teacher/edit/' + str(teacher_pk),
                           'functionality_name': 'Edit Teacher',
                           'form': teacher_edit_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/teacher/edit/' + str(teacher_pk),
                       'functionality_name': 'Edit Teacher',
                       'form': EditTeacherForm(school_pk=school_pk, teacher_pk=teacher_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to edit a teacher")


def teacher_delete(request, teacher_pk):
    authorised = request.session.get('user_type', None) == 'Administrator'
    if authorised:
        administrator = Administrator.objects.get(user=User.objects.get(username=request.session.get('username', None)))
        teacher = Teacher.objects.get(pk=teacher_pk)
        authorised = administrator.school_id == teacher.school_id

    if authorised:
        teacher_to_delete = Teacher.objects.get(pk=teacher_pk)
        teacher_display_text = str(teacher_to_delete)
        if request.POST:
            if teacher_to_delete.delete_teacher_safe():
                context = {'finish_title': 'Teacher Deleted',
                           'user_message': 'Teacher Deleted Successfully: ' + teacher_display_text}
            else:
                context = {'finish_title': 'Teacher Not Deleted',
                           'user_error_message': 'Could Not Delete ' + teacher_display_text
                                                 + ' (Teacher is Assigned to one or more Classes)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/teacher/delete/' + str(teacher_pk),
                       'functionality_name': 'Delete Teacher',
                       'prompt_message': 'Are You Sure You Wish To Delete ' + teacher_display_text + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a teacher from this school")


def teacher_reset_password(request, teacher_pk):
    if request.session.get('user_type', None) == 'Administrator':
        teacher = Teacher.objects.get(pk=teacher_pk)
        if request.POST:
            new_password = teacher.reset_password()
            message = ('username: ' + teacher.user.username + '\n' +
                       'password: ' + new_password)
            send_mail('Fitness Testing App - Teacher Password Reset', message, DEFAULT_FROM_EMAIL, [teacher.email])
            context = {'finish_title': 'Password Reset',
                       'user_message': 'Password Reset For User: ' + str(teacher)}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/teacher/reset_password/' + str(teacher_pk),
                       'functionality_name': 'Reset Password',
                       'prompt_message': 'Are You Sure You Wish To Reset The Password For ' + str(teacher) + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to reset the password for a teacher")


def class_list(request):
    if request.session.get('user_type', None) == 'Administrator':
        username = request.session.get('username', None)
        school = Administrator.objects.get(user=User.objects.get(username=username)).school_id
        context = {
            'item_list': [(class_instance, class_instance.get_display_items())
                          for class_instance in Class.objects.filter(school_id=school)],
            'item_list_title': 'Class List',
            'item_list_table_headings': Class.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['modal_load_link', '/class/add/', 'Add Class'],
                       ['modal_load_link', '/class/adds/', 'Add Classes']]]
            ],
            'item_list_options': [
                ['modal_load_link', '/class/edit/', 'pencil'],
                ['class_load_link', '/class/class/', 'home'],
                ['modal_load_link', '/class/delete/', 'remove']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view class list")


def class_add(request):
    if request.session.get('user_type', None) == 'Administrator':
        user = User.objects.get(username=request.session.get('username', None))
        school_pk = Administrator.objects.get(user=user).school_id.pk
        if request.POST:
            class_add_form = AddClassForm(school_pk=school_pk, data=request.POST)
            if class_add_form.add_class():
                class_display_text = (class_add_form.cleaned_data['class_name'] +
                                      ' (' + class_add_form.cleaned_data['year'] + ')')
                context = {'finish_title': 'Class Added',
                           'user_message': 'Class Added Successfully: ' + class_display_text}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/class/add/',
                           'functionality_name': 'Add Class',
                           'form': class_add_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/add/',
                       'functionality_name': 'Add Class',
                       'form': AddClassForm(school_pk=school_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add a class")


def class_adds(request):
    if request.session.get('user_type', None) == 'Administrator':
        user = User.objects.get(username=request.session.get('username', None))
        school_pk = Administrator.objects.get(user=user).school_id.pk
        if request.POST:
            class_adds_form = AddClassesForm(school_pk=school_pk, data=request.POST, files=request.FILES)
            result = class_adds_form.add_classes(request)
            if result:

                (n_created, teacher_username_not_exist, test_set_not_exist,
                 class_already_exists, invalid_lines) = result
                result_message = ['Classes Created: ' + str(n_created)]
                if len(teacher_username_not_exist) > 0:
                    result_message.append('Could not recognise the teacher username on the following lines:')
                    for line in teacher_username_not_exist:
                        result_message.append(line)
                if len(test_set_not_exist) > 0:
                    result_message.append('Could not recognise the test set on the following lines:')
                    for line in test_set_not_exist:
                        result_message.append(line)
                if len(class_already_exists) > 0:
                    result_message.append('The class year and name already existed for the following lines:')
                    for line in class_already_exists:
                        result_message.append(line)
                if len(invalid_lines) > 0:
                    result_message.append('Error reading data on the following lines:')
                    for line in invalid_lines:
                        result_message.append(line)
                context = {'finish_title': 'Classes Added', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))

            else:
                context = {'post_to_url': '/class/adds/',
                           'functionality_name': 'Add Classes',
                           'form': class_adds_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/adds/',
                       'functionality_name': 'Add Classes',
                       'form': AddClassesForm(school_pk=school_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add classes")


def class_edit(request, class_pk):
    if request.session.get('user_type', None) == 'Administrator':
        user = User.objects.get(username=request.session.get('username', None))
        school_pk = Administrator.objects.get(user=user).school_id.pk
        if request.POST:
            class_edit_form = EditClassForm(school_pk=school_pk, class_pk=class_pk, data=request.POST)
            if class_edit_form.edit_class():
                class_display_text = (class_edit_form.cleaned_data['class_name'] +
                                      ' (' + class_edit_form.cleaned_data['year'] + ')')
                context = {'finish_title': 'Class Edited',
                           'user_message': 'Class Edited Successfully: ' + class_display_text}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/class/edit/' + str(class_pk),
                           'functionality_name': 'Edit Class',
                           'form': class_edit_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/edit/' + str(class_pk),
                       'functionality_name': 'Edit Class',
                       'form': EditClassForm(school_pk=school_pk, class_pk=class_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to edit a class")


def class_delete(request, class_pk):
    if request.session.get('user_type', None) == 'Administrator':
        class_to_delete = Class.objects.get(pk=class_pk)
        class_display_text = (class_to_delete.class_name + ' ' + ' (' + str(class_to_delete.year) + ')')
        if request.POST:
            if class_to_delete.delete_class_safe():
                context = {'finish_title': 'Class Deleted',
                           'user_message': 'Class Deleted Successfully: ' + class_display_text}
            else:
                context = {'finish_title': 'Class Not Deleted',
                           'user_error_message': 'Could Not Delete ' + class_display_text
                                                 + ' (Student Results are Entered for this Class)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/delete/' + str(class_pk),
                       'functionality_name': 'Delete Class',
                       'prompt_message': 'Are You Sure You Wish To Delete ' + class_display_text + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a class")


def class_class(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        display_items = Class.objects.get(pk=class_pk).get_display_items()
        context = {
            'class_title': display_items[1] + ' (' + str(display_items[0]) + ') : ' + str(display_items[2]),
            'class_pk': str(class_pk)
        }
        return render(request, 'class.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view class")


def class_results_table(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        class_instance = Class.objects.get(pk=class_pk)
        class_tests = [class_test.test_name for class_test in ClassTest.objects.filter(class_id=class_instance)]
        student_test_results = [(enrolment.student_id, enrolment.get_test_results()) for enrolment in
                                StudentClassEnrolment.objects.filter(class_id=class_instance)]
        context = {
            'class_tests': class_tests,
            'class_test_options': [
                ['class_results_modal_load_link', '/class/test/delete/' + str(class_pk) + '/', 'remove'],
                ['test_instructions_load_link', '/test/instructions/', 'info-sign']
            ],
            'results_table_buttons': [
                ['+', [['class_results_modal_load_link', '/class/test/add/' + str(class_pk), 'Add Test To Class'],
                       ['class_results_modal_load_link', '/class/test_set/load/' + str(class_pk),
                        'Load Class Tests From A Test Set'],
                       ['class_results_modal_load_link', '/class/test_set/save/' + str(class_pk),
                        'Save Current Class Tests As A Test Set'],
                       ['class_results_modal_load_link', '/class/get_new_code/' + str(class_pk),
                        'Get New Class Login Password']]]
            ],
            'student_test_results': student_test_results
        }
        return render(request, 'class_results_table.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view class results table")


def add_test_to_class(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        if request.POST:
            add_test_to_class_form = AssignTestToClassForm(class_pk=class_pk, data=request.POST)
            if add_test_to_class_form.assign_test_to_class():
                test_added = Test.objects.get(pk=add_test_to_class_form.cleaned_data['test'])
                context = {'finish_title': 'Test Added To Class',
                           'user_message': 'Test Added To Class Successfully: ' + str(test_added)}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/class/test/add/' + str(class_pk) + '/',
                           'functionality_name': 'Add Test To Class',
                           'form': add_test_to_class_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/test/add/' + str(class_pk) + '/',
                       'functionality_name': 'Add Test To Class',
                       'form': AssignTestToClassForm(class_pk=class_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add a test to this class")


def save_class_tests_as_test_set(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        if request.POST:
            save_class_tests_as_test_set_form = SaveClassTestsAsTestSetForm(class_pk=class_pk, data=request.POST)
            if save_class_tests_as_test_set_form.save_class_tests_as_test_set():
                test_set_saved = TestSet.objects.get(
                    school=Class.objects.get(pk=class_pk).school_id,
                    test_set_name=save_class_tests_as_test_set_form.cleaned_data['test_set_name']
                )
                context = {'finish_title': 'Test Set Saved',
                           'user_message': 'Test Set Saved Successfully: ' + str(test_set_saved.test_set_name)}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/class/test_set/save/' + str(class_pk) + '/',
                           'functionality_name': 'Save Test Set',
                           'form': save_class_tests_as_test_set_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/test_set/save/' + str(class_pk) + '/',
                       'functionality_name': 'Save Test Set',
                       'form': SaveClassTestsAsTestSetForm(class_pk=class_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to save a test set from this class")


def load_class_tests_from_test_set(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        if request.POST:
            load_class_tests_from_test_set_form = LoadClassTestsFromTestSetForm(class_pk=class_pk, data=request.POST)
            if load_class_tests_from_test_set_form.load_class_tests_from_test_set():
                test_set_loaded = TestSet.objects.get(
                    school=Class.objects.get(pk=class_pk).school_id,
                    test_set_name=load_class_tests_from_test_set_form.cleaned_data['test_set_name']
                )
                context = {'finish_title': 'Test Set Loaded',
                           'user_message': 'Test Set Loaded Successfully: ' + str(test_set_loaded.test_set_name)}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/class/test_set/load/' + str(class_pk) + '/',
                           'functionality_name': 'Load Test Set',
                           'form': load_class_tests_from_test_set_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/test_set/load/' + str(class_pk) + '/',
                       'functionality_name': 'Load Test Set',
                       'form': LoadClassTestsFromTestSetForm(class_pk=class_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to load a test set to this class")


def remove_test_from_class(request, class_pk, test_pk):
    if user_authorised_for_class(request, class_pk):
        class_instance = Class.objects.get(pk=class_pk)
        test = Test.objects.get(pk=test_pk)
        if request.POST:
            if class_instance.deallocate_test_safe(test):
                context = {'finish_title': 'Remove Test From Class',
                           'user_message': 'Test Removed Successfully: ' + str(test)}
            else:
                context = {'finish_title': 'Test Not Removed From Class',
                           'user_error_message': 'Could Not Remove ' + str(test) + ' (Results Have Been Entered For'
                                                                                   ' This Test In This Class)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/test/delete/' + str(class_pk) + '/' + str(test_pk),
                       'functionality_name': 'Remove Test',
                       'prompt_message': 'Are You Sure You Wish To Remove Test From Class ' + str(test) + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to remove a test from this class")


def get_new_class_code(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        if request.POST:
            context = {'finish_title': 'New Login Password', 'user_message': 'New Login Password Done'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            class_instance = Class.objects.get(pk=class_pk)
            context = {'post_to_url': '/class/get_new_code/' + str(class_pk),
                       'modal_title': 'New Class Login Details',
                       'functionality_name': 'Done',
                       'prompt_messages': ['Username: ' + class_instance.user.username,
                                           'Password: ' + class_instance.reset_code()]}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a teacher from this school")


def remove_student_from_class(request, class_pk, student_pk):
    if user_authorised_for_class(request, class_pk):
        class_instance = Class.objects.get(pk=class_pk)
        student = Student.objects.get(pk=student_pk)
        if request.POST:
            if class_instance.withdraw_student_safe(student):
                context = {'finish_title': 'Remove Student From Class',
                           'user_message': 'Student Removed Successfully: ' + str(student)}
            else:
                context = {'finish_title': 'Student Not Removed From Class',
                           'user_error_message': 'Could Not Remove ' + str(student) + ' (This Student Has Results'
                                                                                      ' Entered In This Class)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/student/delete/' + str(class_pk) + '/' + str(student_pk),
                       'functionality_name': 'Remove Student',
                       'prompt_message': 'Are You Sure You Wish To Remove Student From Class ' + str(student) + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to remove a student from this class")


def user_authorised_for_class(request, class_pk):
    user_type = request.session.get('user_type', None)
    if (user_type == 'Administrator') or (user_type == 'Teacher'):
        user = User.objects.get(username=request.session.get('username', None))
        class_instance = Class.objects.get(pk=class_pk)
        if user_type == 'Administrator':
            administrator_school = Administrator.objects.get(user=user).school_id
            authorised = class_instance.school_id == administrator_school
        else:
            teacher = Teacher.objects.get(user=user)
            authorised = TeacherClassAllocation.objects.filter(class_id=class_instance, teacher_id=teacher).exists()
    else:
        authorised = False

    return authorised