from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.template import RequestContext
from fitness_scoring.models import User, Teacher, Administrator, SuperUser, School, TestCategory, Test, Student, Class
from fitness_scoring.models import TeacherClassAllocation, StudentClassEnrolment, ClassTestSet
from fitness_scoring.forms import AddSchoolForm, AddSchoolsForm, EditSchoolForm
from fitness_scoring.forms import AddTestCategoryForm, AddTestCategoriesForm, EditTestCategoryForm
from fitness_scoring.forms import AddTestsForm, EditTestForm, UpdateTestFromFileForm
from fitness_scoring.forms import AddStudentForm, AddStudentsForm, EditStudentForm
from fitness_scoring.forms import AddTeacherForm, AddTeachersForm, EditTeacherForm
from fitness_scoring.forms import AddClassForm, AddClassesForm, EditClassForm
from fitness_scoring.forms import EnrolStudentInClassForm, EnrolStudentsInClassForm
from fitness_scoring.forms import AssignTestToClassForm, AssignTestsToClassForm
from pe_site.settings import DEFAULT_FROM_EMAIL
from django.core.mail import send_mail


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
            return redirect('fitness_scoring.views.administrator_view')
        elif user_type == 'Teacher':
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

        teacher = Teacher.objects.get(user=User.objects.get(username=request.session.get('username')))
        heading = teacher.first_name + ' ' + teacher.surname + ' (' + teacher.school_id.name + ')'
        context = {
            'logged_in_heading': heading,
            'user_name': request.session.get('username'),
            'user_tab_page_title': heading,
            'user_tabs': [
                ['Home', '/teacher_home/', 'user_home_page'],
                ['Add/Update Student List', '/student/list2/', 'item_list:2'],
            ]
        }

        return render(request, 'user_tab_page.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def teacher_home(request):
    if request.session.get('user_type', None) == 'Teacher':
        teacher = Teacher.objects.get(user=User.objects.get(username=request.session.get('username')))
        heading = teacher.first_name + ' ' + teacher.surname + ' (' + teacher.school_id.name + ')'
        context = {'user_home_page_title': heading,
                   'user_home_page_text': 'Select the view via the navigation side bar to the left'}
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
                ['Add/Update Student List', '/student/list/', 'item_list:2'],
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
        context = {'user_home_page_title': 'Administrator: ' + administrator.school_id.name,
                   'user_home_page_text': 'Select the view via the navigation side bar to the left'}
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
            send_mail('Fitness Testing App - Administrator Login Details', message, DEFAULT_FROM_EMAIL,
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


def student_list(request):
    if request.session.get('user_type', None) == 'Administrator':
        username = request.session.get('username', None)
        school = Administrator.objects.get(user=User.objects.get(username=username)).school_id
        context = {
            'item_list': [(student, student.get_display_items())
                          for student in Student.objects.filter(school_id=school)],
            'item_list_title': 'Student List',
            'item_list_table_headings': Student.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['modal_load_link', '/student/add/', 'Add Student'],
                       ['modal_load_link', '/student/adds/', 'Add/Edit Students From .CSV']]]
            ],
            'item_list_options': [
                ['modal_load_link', '/student/edit/', 'pencil'],
                ['modal_load_link', '/student/delete/', 'remove']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view student list")


def student_list2(request):
    if request.session.get('user_type', None) == 'Teacher':
        username = request.session.get('username', None)
        school = Teacher.objects.get(user=User.objects.get(username=username)).school_id
        context = {
            'item_list': [(student, student.get_display_items())
                          for student in Student.objects.filter(school_id=school)],
            'item_list_title': 'Student List',
            'item_list_table_headings': Student.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['modal_load_link', '/student/add/', 'Add Student']]]
            ],
            'item_list_options': [
                ['modal_load_link', '/student/edit/', 'pencil'],
                ['modal_load_link', '/student/delete/', 'remove']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view student list")


def student_add(request):
    user_type = request.session.get('user_type', None)
    if (user_type == 'Administrator') or (user_type == 'Teacher'):
        user = User.objects.get(username=request.session.get('username', None))
        school_pk = (Administrator.objects.get(user=user) if (user_type == 'Administrator')
                     else Teacher.objects.get(user=user)).school_id.pk
        if request.POST:
            student_add_form = AddStudentForm(school_pk=school_pk, data=request.POST)
            if student_add_form.add_student():
                student_display_text = (student_add_form.cleaned_data['first_name'] + ' ' +
                                        student_add_form.cleaned_data['surname'] + ' (' +
                                        student_add_form.cleaned_data['student_id'] + ')')
                context = {'finish_title': 'Student Added',
                           'user_message': 'Student Added Successfully: ' + student_display_text}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/student/add/',
                           'functionality_name': 'Add Student',
                           'form': student_add_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/student/add/',
                       'functionality_name': 'Add Student',
                       'form': AddStudentForm(school_pk=school_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add a student")


def student_adds(request):
    if request.session.get('user_type', None) == 'Administrator':
        user = User.objects.get(username=request.session.get('username', None))
        school_pk = Administrator.objects.get(user=user).school_id.pk
        if request.POST:
            student_adds_form = AddStudentsForm(school_pk=school_pk, data=request.POST, files=request.FILES)
            result = student_adds_form.add_students(request)
            if result:
                (n_created, n_updated, n_not_created_or_updated) = result
                result_message = ['Students Created: '+str(n_created),
                                  'Students Updated: '+str(n_updated),
                                  'No Changes From Data Lines: '+str(n_not_created_or_updated)]
                context = {'finish_title': 'Students Added/Updated', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/student/adds/',
                           'functionality_name': 'Add Students',
                           'form': student_adds_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/student/adds/',
                       'functionality_name': 'Add Students',
                       'form': AddStudentsForm(school_pk=school_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add students")


def student_edit(request, student_pk):
    user_type = request.session.get('user_type', None)
    authorised = (user_type == 'Administrator') or (user_type == 'Teacher')
    if authorised:
        user = User.objects.get(username=request.session.get('username', None))
        school = (Administrator.objects.get(user=user) if (user_type == 'Administrator')
                  else Teacher.objects.get(user=user)).school_id
        student = Student.objects.get(pk=student_pk)
        authorised = school == student.school_id

    if authorised:
        user = User.objects.get(username=request.session.get('username', None))
        school_pk = (Administrator.objects.get(user=user) if (user_type == 'Administrator')
                     else Teacher.objects.get(user=user)).school_id.pk
        if request.POST:
            student_edit_form = EditStudentForm(school_pk=school_pk, student_pk=student_pk, data=request.POST)
            if student_edit_form.edit_student():
                student_display_text = (student_edit_form.cleaned_data['first_name'] + ' ' +
                                        student_edit_form.cleaned_data['surname'] + ' (' +
                                        student_edit_form.cleaned_data['student_id'] + ')')
                context = {'finish_title': 'Student Edited',
                           'user_message': 'Student Edited Successfully: ' + student_display_text}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/student/edit/' + str(student_pk),
                           'functionality_name': 'Edit Student',
                           'form': student_edit_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/student/edit/' + str(student_pk),
                       'functionality_name': 'Edit Student',
                       'form': EditStudentForm(school_pk=school_pk, student_pk=student_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to edit a student")


def student_delete(request, student_pk):
    user_type = request.session.get('user_type', None)
    authorised = (user_type == 'Administrator') or (user_type == 'Teacher')
    if authorised:
        user = User.objects.get(username=request.session.get('username', None))
        school = (Administrator.objects.get(user=user) if (user_type == 'Administrator')
                  else Teacher.objects.get(user=user)).school_id
        student = Student.objects.get(pk=student_pk)
        authorised = school == student.school_id

    if authorised:
        student_to_delete = Student.objects.get(pk=student_pk)
        student_display_text = str(student_to_delete)
        if request.POST:
            if student_to_delete.delete_student_safe():
                context = {'finish_title': 'Student Deleted',
                           'user_message': 'Student Deleted Successfully: ' + student_display_text}
            else:
                context = {'finish_title': 'Student Not Deleted',
                           'user_error_message': 'Could Not Delete ' + student_display_text
                                                 + ' (Is Enrolled In A Class)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/student/delete/' + str(student_pk),
                       'functionality_name': 'Delete Student',
                       'prompt_message': 'Are You Sure You Wish To Delete ' + student_display_text + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a student")


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
                ['+', [['modal_load_link', '/teacher/add/', 'Add Teacher'],
                       ['modal_load_link', '/teacher/adds/', 'Add/Edit Teachers From .CSV']]]
            ],
            'item_list_options': [
                ['modal_load_link', '/teacher/edit/', 'pencil'],
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


def teacher_adds(request):
    if request.session.get('user_type', None) == 'Administrator':
        user = User.objects.get(username=request.session.get('username', None))
        school_pk = Administrator.objects.get(user=user).school_id.pk
        if request.POST:
            teacher_adds_form = AddTeachersForm(school_pk=school_pk, data=request.POST, files=request.FILES)
            result = teacher_adds_form.add_teachers(request)
            if result:
                (n_created, n_updated, n_not_created_or_updated) = result
                result_message = ['Teachers Created: '+str(n_created),
                                  'Teachers Updated: '+str(n_updated),
                                  'No Changes From Data Lines: '+str(n_not_created_or_updated)]
                context = {'finish_title': 'Teachers Added/Updated', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/teacher/adds/',
                           'functionality_name': 'Add Teachers',
                           'form': teacher_adds_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/teacher/adds/',
                       'functionality_name': 'Add Teachers',
                       'form': AddTeachersForm(school_pk=school_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add teachers")


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
                                                 + ' (Teacher Being Used)'}
            return render(request, 'user_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/teacher/delete/' + str(teacher_pk),
                       'functionality_name': 'Delete Teacher',
                       'prompt_message': 'Are You Sure You Wish To Delete ' + teacher_display_text + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a teacher from this school")


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
                       ['modal_load_link', '/class/adds/', 'Add/Edit Classes From .CSV']]]
            ],
            'item_list_options': [
                ['modal_load_link', '/class/edit/', 'pencil'],
                ['modal_load_link', '/class/delete/', 'remove'],
                ['class_load_link', '/class/class/', 'home']
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
                (n_created, n_updated, n_not_created_or_updated) = result
                result_message = ['Classes Created: '+str(n_created),
                                  'Classes Updated: '+str(n_updated),
                                  'No Changes From Data Lines: '+str(n_not_created_or_updated)]
                context = {'finish_title': 'Classes Added/Updated', 'user_messages': result_message}
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
                                      '(' + class_edit_form.cleaned_data['year'] + ')')
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
                                                 + ' (Class Being Used)'}
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


def students_in_class_list(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        student_enrolments = StudentClassEnrolment.objects.filter(class_id=Class.objects.get(pk=class_pk))
        context = {
            'item_list': [(enrolment.student_id, enrolment.student_id.get_display_items())
                          for enrolment in student_enrolments],
            'item_list_title': 'Students In Class',
            'item_list_table_headings': Student.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['class_student_modal_load_link', '/class/student/add/' + str(class_pk) + '/',
                        'Add Student To Class'],
                       ['class_student_modal_load_link', '/class/student/adds/' + str(class_pk) + '/',
                        'Add Students To Class From .CSV']]]
            ],
            'item_list_options': [
                ['class_student_modal_load_link', '/class/student/delete/' + str(class_pk) + '/', 'remove']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view student list")


def add_student_to_class(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        if request.POST:
            add_student_to_class_form = EnrolStudentInClassForm(class_pk=class_pk, data=request.POST)
            if add_student_to_class_form.enrol_student_in_class():
                student_added = Student.objects.get(pk=add_student_to_class_form.cleaned_data['student'])
                context = {'finish_title': 'Student Added To Class',
                           'user_message': 'Student Added To Class Successfully: ' + str(student_added)}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/class/student/add/' + str(class_pk) + '/',
                           'functionality_name': 'Add Student To Class',
                           'form': add_student_to_class_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/student/add/' + str(class_pk) + '/',
                       'functionality_name': 'Add Student To Class',
                       'form': EnrolStudentInClassForm(class_pk=class_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add a student to this class")


def add_students_to_class(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        if request.POST:
            add_students_to_class_form = EnrolStudentsInClassForm(class_pk=class_pk, data=request.POST,
                                                                  files=request.FILES)
            result = add_students_to_class_form.enrol_students_in_class(request)
            if result:
                (n_created, n_updated, n_not_created_or_updated) = result
                result_message = ['Students Added To Class Created: '+str(n_created),
                                  'No Changes From Data Lines: '+str(n_not_created_or_updated)]
                context = {'finish_title': 'Students Added To Class', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/class/student/adds/' + str(class_pk),
                           'functionality_name': 'Add Students To Class',
                           'form': add_students_to_class_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/student/adds/' + str(class_pk),
                       'functionality_name': 'Add Students To Class',
                       'form': EnrolStudentsInClassForm(class_pk=class_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add students to this class")


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


def tests_for_class_list(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        tests_assigned = ClassTestSet.objects.filter(class_id=Class.objects.get(pk=class_pk))
        context = {
            'item_list': [(assignment.test_name, assignment.test_name.get_display_items())
                          for assignment in tests_assigned],
            'item_list_title': 'Tests For Class',
            'item_list_table_headings': Test.get_display_list_headings(),
            'item_list_buttons': [
                ['+', [['class_test_modal_load_link', '/class/test/add/' + str(class_pk) + '/', 'Add Test To Class'],
                       ['class_test_modal_load_link', '/class/test/adds/' + str(class_pk) + '/',
                        'Add Tests To Class From .CSV']]]
            ],
            'item_list_options': [
                ['class_test_modal_load_link', '/class/test/delete/' + str(class_pk) + '/', 'remove']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to view test list")


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


def add_tests_to_class(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        if request.POST:
            add_tests_to_class_form = AssignTestsToClassForm(class_pk=class_pk, data=request.POST, files=request.FILES)
            result = add_tests_to_class_form.assign_tests_to_class(request)
            if result:
                (n_created, n_updated, n_not_created_or_updated) = result
                result_message = ['Tests Added To Class Created: '+str(n_created),
                                  'No Changes From Data Lines: '+str(n_not_created_or_updated)]
                context = {'finish_title': 'Tests Added To Class', 'user_messages': result_message}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/class/test/adds/' + str(class_pk),
                           'functionality_name': 'Add Tests To Class',
                           'form': add_tests_to_class_form}
                return render(request, 'modal_form.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/class/test/adds/' + str(class_pk),
                       'functionality_name': 'Add Tests To Class',
                       'form': AssignTestsToClassForm(class_pk=class_pk)}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to add tests to this class")


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