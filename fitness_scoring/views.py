from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.template import RequestContext
from fitness_scoring.models import User, Teacher, Administrator, SuperUser, School, Class
from fitness_scoring.models import TestCategory, MajorTestCategory, Test, PercentileBracketList
from fitness_scoring.models import TeacherClassAllocation, ClassTest, StudentClassEnrolment, TestSet
from fitness_scoring.models import StudentClassTestResult
from fitness_scoring.forms import ChangePasswordFrom
from fitness_scoring.forms import AddSchoolForm, AddSchoolsForm, EditSchoolForm
from fitness_scoring.forms import AddTestCategoryForm, AddTestCategoriesForm, EditTestCategoryForm
from fitness_scoring.forms import AddMajorTestCategoryForm, AddMajorTestCategoriesForm, EditMajorTestCategoryForm
from fitness_scoring.forms import AddTestsForm, EditTestForm, UpdateTestFromFileForm
from fitness_scoring.forms import AddTeacherForm, EditTeacherForm
from fitness_scoring.forms import AddClassForm, AddClassesForm, EditClassForm, AddClassTeacherForm, EditClassTeacherForm
from fitness_scoring.forms import AssignTestToClassForm, SaveClassTestsAsTestSetForm, LoadClassTestsFromTestSetForm
from fitness_scoring.forms import ResolveIssuesPersonalForm, ResolveIssuesClassForm
from fitness_scoring.forms import ResolveIssuesSchoolIDForm, ResolveIssuesSchoolNameForm, ResolveIssuesForm
from fitness_scoring.forms import StudentEntryForm, StudentEntryEditForm
from fitness_scoring.user_emails import send_email_user_reset


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


def logout_user(request):
    request.session.flush()
    return redirect('fitness_scoring.views.login_user')


def change_user_password(request, is_finished):
    user_type = request.session.get('user_type', None)
    if (user_type == 'SuperUser') or (user_type == 'Administrator') or (user_type == 'Teacher'):
        if is_finished == 'finished':
            context = {'finish_title': 'Password Changed', 'user_message': 'Password Changed Successfully'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            user_pk = User.objects.get(username=request.session.get('username', None)).pk
            if request.POST:
                change_password_form = ChangePasswordFrom(user_pk=user_pk, data=request.POST)
                if change_password_form.change_password():
                    context = {'post_to_url': '/change_password/finished',
                               'modal_title': 'Password Changed',
                               'functionality_name': 'Done',
                               'prompt_message': 'Password Changed Successfully',
                               'hide_cancel_button': True}
                    return render(request, 'modal_form.html', RequestContext(request, context))
                else:
                    context = {'post_to_url': '/change_password/not_finished',
                               'functionality_name': 'Change Password',
                               'form': change_password_form}
                    return render(request, 'modal_form.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/change_password/not_finished',
                           'functionality_name': 'Change Password',
                           'form': ChangePasswordFrom(user_pk=user_pk)}
                return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to change password")


def class_student_view(request):
    if request.session.get('user_type', None) == 'Class':
        user = User.objects.get(username=request.session.get('username', None))
        class_instance = Class.objects.get(user=user)
        context = {'post_to_url': '/class_student_view/',
                   'school_name': class_instance.school_id.name,
                   'class_name': class_instance.class_name}
        if request.POST:
            if request.POST.get('results_done_button'):
                return redirect('fitness_scoring.views.logout_user')
            elif request.POST.get('results_cancel_button'):
                context['user_message'] = 'Results were not entered'
                return render(request, 'student_entry_form.html', RequestContext(request, context))
            else:
                form = StudentEntryForm(class_pk=class_instance.pk, data=request.POST)
                if form.save_student_entry():
                    context['user_message'] = 'Your results have been entered'
                    return render(request, 'student_entry_form.html', RequestContext(request, context))
                else:
                    context['form'] = form
                    return render(request, 'student_entry_form.html', RequestContext(request, context))
        else:
            context['form'] = StudentEntryForm(class_pk=class_instance.pk)
            return render(request, 'student_entry_form.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def class_student_results_view(request, enrolment_pk):
    enrolment = StudentClassEnrolment.objects.get(pk=enrolment_pk)
    test_results = StudentClassTestResult.objects.filter(student_class_enrolment=enrolment)
    major_test_categories = set([str(a.test.major_test_category).replace(" ", "_") for a in test_results])
    mtc_tc = set([(str(a.test.major_test_category).replace(" ", "_"),
                  str(a.test.test_category).replace(" ", "_")) for a in test_results])
    results_for_context = [(str(result.test.major_test_category).replace(" ", "_"),
                            str(result.test.test_category).replace(" ", "_"),
                            result.test.test_name,
                            result.percentile,
                            result.result) for result in test_results]

    context = {'student_name': enrolment.student_id,
               'gender': enrolment.student_gender_at_time_of_enrolment,
               'major_test_categories': major_test_categories,
               'mtc_tc': mtc_tc,
               'results': sorted(results_for_context)
               }
    return render(request, 'class_student_results.html', RequestContext(request, context))


def teacher_view(request):
    if request.session.get('user_type', None) == 'Teacher':

        teacher = Teacher.objects.get(user=User.objects.get(username=request.session.get('username')))
        heading = teacher.first_name + ' ' + teacher.surname + ' (' + teacher.school_id.name + ')'
        context = {
            'logged_in_heading': heading,
            'user_name': request.session.get('username'),
            'user_tab_page_title': heading,
            'user_tabs': [
                ['Home', '/teacher_home/', 'user_home_page'],
                ['Add/Update Class List', '/class/list/', 'item_list:2']
            ]
        }

        return render(request, 'user_tab_page.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def teacher_home(request):
    if request.session.get('user_type', None) == 'Teacher':

        teacher = Teacher.objects.get(user=User.objects.get(username=request.session.get('username')))

        steps = [('Change Password', 'change_password'),
                 ('Add Classes For Year', 'teacher_add_classes'),
                 ('Add Tests To Classes For The Year', 'teacher_add_tests'),
                 ('Run Tests (*temp* see my sheet for what instructions should contain *temp*)', 'teacher_run_tests'),
                 ('Get Students To Enter Results', 'teacher_student_enter_results'),
                 ('Approve Entries For Class', 'teacher_approve_entries'),
                 ('View Results', 'teacher_view_results')]
        non_optional_steps = 7
        steps_formatted = []
        for step_index in range(non_optional_steps):
            (step_text, instructions_name) = steps[step_index]
            steps_formatted.append(('Step ' + str(step_index) + ': ' + step_text,
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
                ['Add/Update Teacher List', '/teacher/list/', 'item_list:3'],
                ['Add/Update Class List', '/class/list/', 'item_list:3']
            ]
        }

        return render(request, 'user_tab_page.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def administrator_home(request):
    if request.session.get('user_type', None) == 'Administrator':

        administrator = Administrator.objects.get(user=User.objects.get(username=request.session.get('username')))

        steps = [('Change Password', 'change_password'),
                 ('Add Teachers', 'administrator_add_teacher'),
                 ('Add Classes For Teachers For The Year', 'administrator_add_classes'),
                 ('Add Tests To Classes For The Year', 'administrator_add_tests')]
        non_optional_steps = 2
        steps_formatted = []
        for step_index in range(non_optional_steps):
            (step_text, instructions_name) = steps[step_index]
            steps_formatted.append(('Step ' + str(step_index) + ': ' + step_text,
                                    '/instructions_page/' + instructions_name))
        steps_optional_formatted = []
        for step_index in range(non_optional_steps, len(steps)):
            (step_text, instructions_name) = steps[step_index]
            steps_optional_formatted.append(('Step ' + str(step_index) + ': ' + step_text,
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
                ['Add/Update School List', '/school/list/', 'item_list:3'],
                ['Add/Update Test List', '/test/list/', 'item_list:4'],
                ['Add/Update Test Category List', '/test_category/list/', 'item_list:2'],
                ['Add/Update Major Test Category List', '/major_test_category/list/', 'item_list:2']
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
    if (instructions_name == 'change_password') and (user_type in ('Administrator', 'Teacher')):
        return render(request, 'instructions/no_instructions.html', RequestContext(request, {}))
    elif (instructions_name == 'administrator_add_teacher') and user_type == 'Administrator':
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
                ['+', [['item_list_modal_load_link', '/school/add/', 'Add School'],
                       ['item_list_modal_load_link', '/school/adds/', 'Add/Edit Schools From .CSV']]]
            ],
            'item_list_options': [
                ['item_list_modal_load_link', '/school/edit/', 'pencil', 'edit school'],
                ['item_list_modal_load_link', '/school/reset_password/', 'repeat', 'reset administrator password'],
                ['item_list_modal_load_link', '/school/delete/', 'remove', 'delete school']
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
            school_adds_form = AddSchoolsForm(data=request.POST, files=request.FILES)
            result = school_adds_form.add_schools(request)
            if result:

                (n_created, school_name_not_exceed_three_characters, invalid_state,
                 invalid_email, error_adding_school, invalid_lines, same_name_warning) = result

                problem_types = [(school_name_not_exceed_three_characters,
                                  'School name did not exceed 3 characters on the following lines:'),
                                 (invalid_state, 'Could not recognise the state on the following lines:'),
                                 (invalid_email, 'Invalid email on the following lines:'),
                                 (invalid_lines, 'Error reading data on the following lines:'),
                                 (same_name_warning, 'Warning the following schools have the same name and state as'
                                                     ' others already in the database:')]

                result_message = [('Schools Created: ' + str(n_created), True)]
                for problem_type, heading in problem_types:
                    if len(problem_type) > 0:
                        result_message.append((heading, True))
                        for line in problem_type:
                            result_message.append((line, False))

                context = {'finish_title': 'Schools Added', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))

            elif result is None:
                context = {'finish_title': 'Schools Not Added',
                           'user_error_message': 'Schools Not Added: Error Reading File'}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/school/adds/',
                           'functionality_name': 'Add Schools',
                           'form': school_adds_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/school/adds/',
                       'functionality_name': 'Add Schools',
                       'form': AddSchoolsForm()}
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
            error_message = school_to_delete.delete_school_errors()
            if error_message:
                context = {'finish_title': 'School Not Deleted',
                           'user_error_message': 'Could Not Delete ' + school_name + ' (' + error_message + ')'}
            elif school_to_delete.delete_school_safe():
                context = {'finish_title': 'School Deleted',
                           'user_message': 'School Deleted Successfully: ' + school_name}
            else:
                context = {'finish_title': 'School Not Deleted',
                           'user_error_message': 'Could Not Delete ' + school_name + ' (Delete Not Safe)'}
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
            send_email_user_reset(administrator.email, administrator.user.username, new_password, False)
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
                ['+', [['item_list_modal_load_link', '/test_category/add/', 'Add Test Category'],
                       ['item_list_modal_load_link', '/test_category/adds/', 'Add/Edit Test Categories From .CSV']]]
            ],
            'item_list_options': [
                ['item_list_modal_load_link', '/test_category/edit/', 'pencil', 'edit test category'],
                ['item_list_modal_load_link', '/test_category/delete/', 'remove', 'delete test category']
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
            test_category_adds_form = AddTestCategoriesForm(data=request.POST, files=request.FILES)
            result = test_category_adds_form.add_test_categories(request)
            if result:

                (n_created, n_blank, test_category_already_exist, invalid_lines) = result

                problem_types = [(test_category_already_exist, 'Test category already existed on the following lines:'),
                                 (invalid_lines, 'Error reading data on the following lines:')]

                result_message = [('Tests Categories Created: ' + str(n_created), True),
                                  ('Lines With Blank Test Category: ' + str(n_blank), True)]
                for problem_type, heading in problem_types:
                    if len(problem_type) > 0:
                        result_message.append((heading, True))
                        for line in problem_type:
                            result_message.append((line, False))

                context = {'finish_title': 'Test Categories Added', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))

            elif result is None:
                context = {'finish_title': 'Test Categories Not Added',
                           'user_error_message': 'Test Categories Not Added: Error Reading File'}
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
            error_message = test_category_to_delete.delete_test_category_errors()
            if error_message:
                context = {'finish_title': 'Test Category Not Deleted',
                           'user_error_message': 'Could Not Delete ' + test_category_name + ' (' + error_message + ')'}
            elif test_category_to_delete.delete_test_category_safe():
                context = {'finish_title': 'Test Category Deleted',
                           'user_message': 'Test Category Deleted Successfully: ' + test_category_name}
            else:
                context = {'finish_title': 'Test Category Not Deleted',
                           'user_error_message': 'Could Not Delete ' + test_category_name + ' (Delete Not Safe)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/test_category/delete/' + str(test_category_pk),
                       'functionality_name': 'Delete Test Category',
                       'prompt_message': 'Are You Sure You Wish To Delete ' + test_category_name + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a test category")


def major_test_category_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(major_test_category, major_test_category.get_display_items())
                          for major_test_category in MajorTestCategory.objects.all()],
            'item_list_title': 'Major Test Category List',
            'item_list_table_headings': MajorTestCategory.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['item_list_modal_load_link', '/major_test_category/add/', 'Add Major Test Category'],
                       ['item_list_modal_load_link', '/major_test_category/adds/', 'Add/Edit Major Test Categories From'
                                                                                   ' .CSV']]]
            ],
            'item_list_options': [
                ['item_list_modal_load_link', '/major_test_category/edit/', 'pencil', 'edit major test category'],
                ['item_list_modal_load_link', '/major_test_category/delete/', 'remove', 'delete major test category']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view major test category list")


def major_test_category_add(request):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            major_test_category_add_form = AddMajorTestCategoryForm(request.POST)
            if major_test_category_add_form.add_major_test_category():
                context = {'finish_title': 'Major Test Category Added',
                           'user_message': 'Major Test Category Added Successfully: '
                                           + major_test_category_add_form.cleaned_data['major_test_category_name']}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/major_test_category/add/',
                           'functionality_name': 'Add Major Test Category',
                           'form': major_test_category_add_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/major_test_category/add/',
                       'functionality_name': 'Add Major Test Category',
                       'form': AddMajorTestCategoryForm()}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add a major test category")


def major_test_category_adds(request):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            major_test_category_adds_form = AddMajorTestCategoriesForm(data=request.POST, files=request.FILES)
            result = major_test_category_adds_form.add_major_test_categories(request)
            if result:

                (n_created, n_blank, major_test_category_already_exist, invalid_lines) = result

                problem_types = [(major_test_category_already_exist, 'Test category already existed on the following'
                                                                     ' lines:'),
                                 (invalid_lines, 'Error reading data on the following lines:')]

                result_message = [('Tests Categories Created: ' + str(n_created), True),
                                  ('Lines With Blank Major Test Category: ' + str(n_blank), True)]
                for problem_type, heading in problem_types:
                    if len(problem_type) > 0:
                        result_message.append((heading, True))
                        for line in problem_type:
                            result_message.append((line, False))

                context = {'finish_title': 'Major Test Categories Added', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))

            elif result is None:
                context = {'finish_title': 'Major Test Categories Not Added',
                           'user_error_message': 'Major Test Categories Not Added: Error Reading File'}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/major_test_category/adds/',
                           'functionality_name': 'Add Major Test Categories',
                           'form': major_test_category_adds_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/major_test_category/adds/',
                       'functionality_name': 'Add Major Test Categories',
                       'form': AddMajorTestCategoriesForm()}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add major test categories")


def major_test_category_edit(request, major_test_category_pk):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            major_test_category_edit_form = EditMajorTestCategoryForm(major_test_category_pk=major_test_category_pk,
                                                                      data=request.POST)
            if major_test_category_edit_form.edit_major_test_category():
                context = {'finish_title': 'Major Test Category Edited',
                           'user_message': 'Major Test Category Edited Successfully: '
                                           + major_test_category_edit_form.cleaned_data['major_test_category_name']}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/major_test_category/edit/' + str(major_test_category_pk),
                           'functionality_name': 'Edit Major Test Category',
                           'form': major_test_category_edit_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/major_test_category/edit/' + str(major_test_category_pk),
                       'functionality_name': 'Edit Major Test Category',
                       'form': EditMajorTestCategoryForm(major_test_category_pk=major_test_category_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to edit a major test category")


def major_test_category_delete(request, major_test_category_pk):
    if request.session.get('user_type', None) == 'SuperUser':
        major_test_category_to_delete = MajorTestCategory.objects.get(pk=major_test_category_pk)
        major_test_category_name = major_test_category_to_delete.major_test_category_name
        if request.POST:
            error_message = major_test_category_to_delete.delete_major_test_category_errors()
            if error_message:
                context = {'finish_title': 'Major Test Category Not Deleted',
                           'user_error_message': 'Could Not Delete ' + major_test_category_name + ' (' + error_message +
                                                 ')'}
            elif major_test_category_to_delete.delete_major_test_category_safe():
                context = {'finish_title': 'Major Test Category Deleted',
                           'user_message': 'Major Test Category Deleted Successfully: ' + major_test_category_name}
            else:
                context = {'finish_title': 'Major Test Category Not Deleted',
                           'user_error_message': 'Could Not Delete ' + major_test_category_name + ' (Delete Not Safe)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/major_test_category/delete/' + str(major_test_category_pk),
                       'functionality_name': 'Delete Major Test Category',
                       'prompt_message': 'Are You Sure You Wish To Delete ' + major_test_category_name + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a major test category")


def test_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(test, test.get_display_items())
                          for test in Test.objects.all()],
            'item_list_title': 'Test List',
            'item_list_table_headings': Test.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['item_list_modal_load_link', '/test/adds/', 'Add Tests From .CSVs']]]
            ],
            'item_list_options': [
                ['item_list_modal_load_link', '/test/edit/', 'pencil', 'edit test'],
                ['item_list_modal_load_link', '/test/update/', 'plus', 'add to percentile brackets'],
                ['percentile_load_link', '/test/percentile_brackets_graphs/None/', 'stats', 'view percentile brackets'],
                ['item_list_modal_load_link', '/test/delete/', 'remove', 'delete test']
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

                (n_created, test_name_already_exists, error_reading_file, problems_in_files) = result

                problem_types = [(test_name_already_exists, 'Test name already exists for the following files:'),
                                 (error_reading_file, 'Error reading the following files:')]
                for file_name, problems_in_data in problems_in_files:
                    problem_types.append((problems_in_data,
                                          'Specific problems were found in the following file: ' + file_name))

                result_message = [('Tests Created: ' + str(n_created), True)]
                for problem_type, heading in problem_types:
                    if len(problem_type) > 0:
                        result_message.append((heading, True))
                        for line in problem_type:
                            result_message.append((line, False))

                context = {'finish_title': 'Tests Added', 'user_messages': result_message}
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
            result = test_update_form.update_test(request)
            if result:

                (problems_in_data, error_line) = result

                result_message = []
                if len(problems_in_data) > 0:
                    result_message.append(('The following problems were found in the file:', True))
                    for problem in problems_in_data:
                        result_message.append((problem, False))
                elif error_line:
                    result_message.append((error_line, True))
                else:
                    result_message.append(('Test Updated Successfully', False))

                context = {'finish_title': 'Test Updated Attempt',
                           'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))

            elif result is None:
                context = {'finish_title': 'Test Not Updated',
                           'user_error_message': 'Test Not Updated: Error Reading File'}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/test/update/' + str(test_pk),
                           'functionality_name': 'Update Test',
                           'form': test_update_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
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
            error_message = test_to_delete.delete_test_errors()
            if error_message:
                context = {'finish_title': 'Test Not Deleted',
                           'user_error_message': 'Could Not Delete ' + test_name + ' (' + error_message + ')'}
            elif test_to_delete.delete_test_safe():
                context = {'finish_title': 'Test Deleted',
                           'user_message': 'Test Deleted Successfully: ' + test_name}
            else:
                context = {'finish_title': 'Test Not Deleted',
                           'user_error_message': 'Could Not Delete ' + test_name + ' (Delete Not Safe)'}
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
        percentile_bracket_list = PercentileBracketList.objects.get(pk=pk_local)
        context = {'test_label': str(test),
                   'result_unit': percentile_bracket_list.percentile_bracket_set.get_result_unit_text(),
                   'age_gender_options': [('/test/percentile_brackets_graphs/' + str(bracket.pk) + '/' + str(test_pk),
                                           '(' + str(bracket.age) + ', ' + bracket.gender + ')',
                                           bracket.pk == pk_local) for bracket in percentile_bracket_lists],
                   'percentile_bracket_scores': percentile_bracket_list.get_scores(True)}
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
                ['+', [['item_list_modal_load_link', '/teacher/add/', 'Add Teacher']]]
            ],
            'item_list_options': [
                ['item_list_modal_load_link', '/teacher/edit/', 'pencil', 'edit teacher'],
                ['item_list_modal_load_link', '/teacher/reset_password/', 'repeat', 'reset teacher password'],
                ['item_list_modal_load_link', '/teacher/delete/', 'remove', 'delete teacher']
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
    if user_authorised_for_teacher(request, teacher_pk):
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
    if user_authorised_for_teacher(request, teacher_pk):
        teacher_to_delete = Teacher.objects.get(pk=teacher_pk)
        teacher_display_text = str(teacher_to_delete)
        if request.POST:
            error_message = teacher_to_delete.delete_teacher_errors()
            if error_message:
                context = {'finish_title': 'Teacher Not Deleted',
                           'user_error_message': 'Could Not Delete ' + teacher_display_text +
                                                 ' (' + error_message + ')'}
            elif teacher_to_delete.delete_teacher_safe():
                context = {'finish_title': 'Teacher Deleted',
                           'user_message': 'Teacher Deleted Successfully: ' + teacher_display_text}
            else:
                context = {'finish_title': 'Teacher Not Deleted',
                           'user_error_message': 'Could Not Delete ' + teacher_display_text + ' (Delete Not Safe)'}
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
            send_email_user_reset(teacher.email, teacher.user.username, new_password, True)
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
    user_type = request.session.get('user_type', None)
    if (user_type == 'Administrator') or (user_type == 'Teacher'):
        user = User.objects.get(username=request.session.get('username', None))
        item_list_add_button_options = [['item_list_modal_load_link', '/class/add/', 'Add Class']]
        if user_type == 'Teacher':
            teacher = Teacher.objects.get(user=user)
            class_items = [(allocation.class_id, allocation.class_id.get_display_items_teacher())
                           for allocation in TeacherClassAllocation.objects.filter(teacher_id=teacher)]
            class_list_headings = Class.get_display_list_headings_teacher()
        else:
            school = Administrator.objects.get(user=user).school_id
            class_items = [(class_instance, class_instance.get_display_items()) for class_instance
                           in Class.objects.filter(school_id=school)]
            class_list_headings = Class.get_display_list_headings()
            item_list_add_button_options.append(['item_list_modal_load_link', '/class/adds/', 'Add Classes'])
        context = {
            'item_list': class_items,
            'item_list_title': 'Class List',
            'item_list_table_headings': class_list_headings,
            'item_list_buttons': [
                ['+', item_list_add_button_options]
            ],
            'item_list_options': [
                ['item_list_modal_load_link', '/class/edit/', 'pencil', 'edit class'],
                ['class_load_link', '/class/class/', 'home', 'go to class page'],
                ['item_list_modal_load_link', '/class/delete/', 'remove', 'delete class']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view class list")


def class_add(request):
    user_type = request.session.get('user_type', None)
    if (user_type == 'Administrator') or (user_type == 'Teacher'):
        user = User.objects.get(username=request.session.get('username', None))
        teacher_or_administrator = (Teacher if user_type == 'Teacher' else Administrator).objects.get(user=user)
        school_pk = teacher_or_administrator.school_id.pk
        if request.POST:
            class_add_form = (AddClassTeacherForm(teacher_pk=teacher_or_administrator.pk, data=request.POST)
                              if user_type == 'Teacher' else AddClassForm(school_pk=school_pk, data=request.POST))
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
            class_add_form = (AddClassTeacherForm(teacher_pk=teacher_or_administrator.pk) if user_type == 'Teacher'
                              else AddClassForm(school_pk=school_pk))
            context = {'post_to_url': '/class/add/',
                       'functionality_name': 'Add Class',
                       'form': class_add_form}
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
                 class_already_exists, invalid_lines, not_current_year_warning) = result

                problem_types = [(teacher_username_not_exist,
                                  'Could not recognise the teacher username on the following lines:'),
                                 (test_set_not_exist, 'Could not recognise the test set on the following lines:'),
                                 (class_already_exists,
                                  'The class year and name already existed for the following lines:'),
                                 (invalid_lines, 'Error reading data on the following lines:'),
                                 (not_current_year_warning, 'Warning the following classes were added not for the'
                                                            ' current year:')]

                result_message = [('Classes Created: ' + str(n_created), True)]
                for problem_type, heading in problem_types:
                    if len(problem_type) > 0:
                        result_message.append((heading, True))
                        for line in problem_type:
                            result_message.append((line, False))

                context = {'finish_title': 'Classes Added', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))

            elif result is None:
                context = {'finish_title': 'Classes Not Added',
                           'user_error_message': 'Classes Not Added: Error Reading File'}
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
    if user_authorised_for_class(request, class_pk):
        user_type = request.session.get('user_type', None)
        user = User.objects.get(username=request.session.get('username', None))
        teacher_or_administrator = (Teacher if user_type == 'Teacher' else Administrator).objects.get(user=user)
        school_pk = teacher_or_administrator.school_id.pk
        if request.POST:
            class_edit_form = (EditClassTeacherForm(teacher_pk=teacher_or_administrator.pk, class_pk=class_pk,
                                                    data=request.POST) if user_type == 'Teacher'
                               else EditClassForm(school_pk=school_pk, class_pk=class_pk, data=request.POST))
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
            class_edit_form = (EditClassTeacherForm(teacher_pk=teacher_or_administrator.pk, class_pk=class_pk)
                               if user_type == 'Teacher' else EditClassForm(school_pk=school_pk, class_pk=class_pk))
            context = {'post_to_url': '/class/edit/' + str(class_pk),
                       'functionality_name': 'Edit Class',
                       'form': class_edit_form}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to edit a class")


def class_delete(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        class_to_delete = Class.objects.get(pk=class_pk)
        class_display_text = (class_to_delete.class_name + ' ' + ' (' + str(class_to_delete.year) + ')')
        if request.POST:
            error_message = class_to_delete.delete_class_errors()
            if error_message:
                context = {'finish_title': 'Class Not Deleted',
                           'user_error_message': 'Could Not Delete ' + class_display_text + ' (' + error_message + ')'}
            elif class_to_delete.delete_class_safe():
                context = {'finish_title': 'Class Deleted',
                           'user_message': 'Class Deleted Successfully: ' + class_display_text}
            else:
                context = {'finish_title': 'Class Not Deleted',
                           'user_error_message': 'Could Not Delete ' + class_display_text + ' (Delete Not Safe)'}
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
        student_test_results = []
        for enrolment in StudentClassEnrolment.objects.filter(class_id=class_instance):
            if enrolment.has_pending_issues():
                approval_option = ['class_results_modal_load_link', '/class_enrolment/resolve_pending_issues/',
                                   'exclamation-sign', 'student result entry has pending issues' + '\n' +
                                                       'click to resolve issues']
            elif enrolment.is_approved():
                approval_option = ['class_results_modal_load_link', '/class_enrolment/un_approve/',
                                   'check', 'student result entry approved' + '\n' + 'click to remove approval']
            else:
                approval_option = ['class_results_modal_load_link', '/class_enrolment/approve/',
                                   'unchecked', 'student result entry not yet approved' + '\n' + 'click to approve']
            student_test_results.append(([approval_option], enrolment.pk, enrolment.student_id,
                                         enrolment.student_gender_at_time_of_enrolment,
                                         enrolment.get_student_age_at_time_of_enrolment(),
                                         enrolment.get_test_results(True)))
        context = {
            'class_tests': class_tests,
            'class_test_options': [
                ['test_instructions_load_link', '/test/instructions/', 'info-sign', 'see instructions for test'],
                ['class_results_modal_load_link', '/class/test/delete/' + str(class_pk) + '/',
                 'remove', 'remove test from class']
            ],
            'enrolment_options': [
                ['class_result_edit_page_load_link', '/class_enrolment/edit/', 'pencil', 'edit student result entry'],
                ['class_results_modal_load_link', '/class_enrolment/delete/', 'remove', 'delete student result entry']
            ],
            'results_table_buttons': [
                ['plus', [['class_results_modal_load_link', '/class/test/add/' + str(class_pk), 'Add Test To Class'],
                          ['class_results_modal_load_link', '/class/test_set/load/' + str(class_pk),
                           'Load Class Tests From A Test Set']]],
                ['asterisk', [['class_results_modal_load_link', '/class/test_set/save/' + str(class_pk),
                               'Save Current Class Tests As A Test Set'],
                              ['modal_load_link', '/class/get_new_code/' + str(class_pk),
                               'Get New Class Login Password'],
                              ['class_results_modal_load_link', '/class/approve_all/' + str(class_pk),
                               'Approve All Student Result Entries For Class']]]
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
                                           'Password: ' + class_instance.reset_code()],
                       'hide_cancel_button': True}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a teacher from this school")


def approve_all_class_results(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        class_instance = Class.objects.get(pk=class_pk)
        if request.POST:
            if class_instance.approve_all_results():
                context = {'finish_title': 'All Student Entry Results Approved',
                           'user_message': 'All Student Entry Results Approved Successfully'}
            else:
                context = {'finish_title': 'Student Entry Results Not Approved',
                           'user_error_message': 'Could Not Approve Student Entry Results'
                                                 ' (Some Entries Have Pending Issues)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/approve_all/' + str(class_pk),
                       'functionality_name': 'Approve All Student Entry Results',
                       'prompt_message': 'Are You Sure You Wish To Approve All Student Entry Results For The Class?'}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to approve all student entry results for this class")


def remove_test_from_class(request, class_pk, test_pk):
    if user_authorised_for_class(request, class_pk):
        class_instance = Class.objects.get(pk=class_pk)
        test = Test.objects.get(pk=test_pk)
        if request.POST:
            error_message = class_instance.deallocate_test_errors(test)
            if error_message:
                context = {'finish_title': 'Test Not Removed From Class',
                           'user_error_message': 'Could Not Remove ' + str(test) + ' (' + error_message + ')'}
            elif class_instance.deallocate_test_safe(test):
                context = {'finish_title': 'Remove Test From Class',
                           'user_message': 'Test Removed Successfully: ' + str(test)}
            else:
                context = {'finish_title': 'Test Not Removed From Class',
                           'user_error_message': 'Could Not Remove ' + str(test) + ' (Delete Not Safe)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/test/delete/' + str(class_pk) + '/' + str(test_pk),
                       'functionality_name': 'Remove Test',
                       'prompt_message': "Are You Sure You Wish To Remove The Test '" + test.test_name +
                                         "' From This Class?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to remove a test from this class")


def class_enrolment_approve(request, enrolment_pk):
    enrolment = StudentClassEnrolment.objects.get(pk=enrolment_pk)
    if user_authorised_for_class(request, enrolment.class_id.pk):
        if request.POST:
            if enrolment.approve_student_results():
                context = {'finish_title': 'Student Result Entry Approved',
                           'user_message': 'Student Result Entry Approved Successfully'}
            else:
                context = {'finish_title': 'Student Result Entry Not Approved',
                           'user_error_message': 'Could Not Approved Student Result Entry (Has Pending Issues)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class_enrolment/approve/' + str(enrolment_pk),
                       'functionality_name': 'Approve Student Result Entry',
                       'prompt_message': 'Are You Sure You Wish To Approve Student Result Entry ' +
                                         str(enrolment.student_id) + '?'}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to approve a student result entry from this class")


def class_enrolment_un_approve(request, enrolment_pk):
    enrolment = StudentClassEnrolment.objects.get(pk=enrolment_pk)
    if user_authorised_for_class(request, enrolment.class_id.pk):
        if request.POST:
            if enrolment.un_approve_student_results():
                context = {'finish_title': 'Student Result Entry Approval Removed',
                           'user_message': 'Student Result Entry Approval Removed Successfully'}
            else:
                context = {'finish_title': 'Student Result Entry Approval Not Removed',
                           'user_error_message': 'Could Not Remove Student Result Entry Approval (Has Pending Issues)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class_enrolment/un_approve/' + str(enrolment_pk),
                       'functionality_name': 'Remove Student Result Entry Approval',
                       'prompt_message': 'Are You Sure You Wish To Remove Student Result Entry Approval For ' +
                                         str(enrolment.student_id) + '?'}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to remove a student result entry approval from this class")


def class_enrolment_resolve_pending_issues(request, enrolment_pk):
    enrolment = StudentClassEnrolment.objects.get(pk=enrolment_pk)
    if user_authorised_for_class(request, enrolment.class_id.pk) and enrolment.has_pending_issues():
        if request.POST:
            if request.POST['resolver_type'] == 'find_solution':
                if enrolment.student_id.has_pending_issues_id():
                    resolve_pending_issues_form = ResolveIssuesSchoolIDForm(enrolment_pk=enrolment_pk,
                                                                            data=request.POST)
                else:
                    resolve_pending_issues_form = ResolveIssuesSchoolNameForm(enrolment_pk=enrolment_pk,
                                                                              data=request.POST)
                resolve_method = resolve_pending_issues_form.find_solution()
                if resolve_method:
                    resolve_pending_issues_form = ResolveIssuesForm(enrolment_pk=enrolment_pk,
                                                                    resolve_method=resolve_method)
            else:
                if enrolment.student_id.has_pending_issues():
                    resolve_pending_issues_form = ResolveIssuesForm(enrolment_pk=enrolment_pk,
                                                                    resolve_method=request.POST['resolve_method'],
                                                                    data=request.POST)
                elif enrolment.pending_issue_other_class_member:
                    resolve_pending_issues_form = ResolveIssuesClassForm(enrolment_pk=enrolment_pk, data=request.POST)
                else:
                    resolve_pending_issues_form = ResolveIssuesPersonalForm(enrolment_pk=enrolment_pk,
                                                                            data=request.POST)

                if resolve_pending_issues_form.resolve_issues():
                    context = {'finish_title': 'Issue Resolved', 'user_message': 'Issue Resolved Successfully'}
                    return render(request, 'user_message.html', RequestContext(request, context))
        else:
            if enrolment.student_id.has_pending_issues_id():
                resolve_pending_issues_form = ResolveIssuesSchoolIDForm(enrolment_pk=enrolment_pk)
            elif enrolment.student_id.has_pending_issues_name():
                resolve_pending_issues_form = ResolveIssuesSchoolNameForm(enrolment_pk=enrolment_pk)
            elif enrolment.pending_issue_other_class_member:
                resolve_pending_issues_form = ResolveIssuesClassForm(enrolment_pk=enrolment_pk)
            else:
                resolve_pending_issues_form = ResolveIssuesPersonalForm(enrolment_pk=enrolment_pk)

        context = {'post_to_url': '/class_enrolment/resolve_pending_issues/' + str(enrolment_pk),
                   'functionality_name': 'Resolve Pending Issue',
                   'form': resolve_pending_issues_form}
        return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("Either there is no issue to resolve or you are not authorised to resolve"
                                     " a pending issue for this class")


def class_enrolment_edit(request, enrolment_pk):
    enrolment = StudentClassEnrolment.objects.get(pk=enrolment_pk)
    if user_authorised_for_class(request, enrolment.class_id.pk):
        class_instance = enrolment.class_id
        context = {'post_to_url': '/class_enrolment/edit/' + str(enrolment_pk),
                   'school_name': class_instance.school_id.name,
                   'class_name': class_instance.class_name,
                   'form_class': 'load_in_class_page',
                   'hide_cancel_button': 'True'}
        if request.POST:
            if request.POST.get('results_cancel_button'):
                return redirect('fitness_scoring.views.class_results_table', class_pk=class_instance.pk)
            else:
                form = StudentEntryEditForm(enrolment_pk=enrolment_pk, data=request.POST)
                if form.edit_student_entry():
                    return redirect('fitness_scoring.views.class_results_table', class_pk=class_instance.pk)
                else:
                    context['form'] = form
                    return render(request, 'student_entry_form_inner.html', RequestContext(request, context))
        else:
            context['form'] = StudentEntryEditForm(enrolment_pk=enrolment_pk)
            return render(request, 'student_entry_form_inner.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to edit a student result entry from this class")


def class_enrolment_delete(request, enrolment_pk):
    enrolment = StudentClassEnrolment.objects.get(pk=enrolment_pk)
    if user_authorised_for_class(request, enrolment.class_id.pk):
        if request.POST:
            enrolment.delete_student_class_enrolment_safe()
            context = {'finish_title': 'Student Result Entry Deleted',
                       'user_message': 'Student Result Entry Deleted Successfully'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class_enrolment/delete/' + str(enrolment_pk),
                       'functionality_name': 'Delete Student Result Entry',
                       'prompt_message': 'Are You Sure You Wish To Delete Student Result Entry ' +
                                         str(enrolment.student_id) + '?'}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a student result entry from this class")


def user_authorised_for_teacher(request, teacher_pk):

    if request.session.get('user_type', None) == 'Administrator':
        administrator = Administrator.objects.get(user=User.objects.get(username=request.session.get('username', None)))
        teacher = Teacher.objects.get(pk=teacher_pk)
        authorised = administrator.school_id == teacher.school_id
    else:
        authorised = False

    return authorised


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