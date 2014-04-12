from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.template import RequestContext
from fitness_scoring.models import User, Teacher, Administrator, SuperUser, School
from fitness_scoring.forms import AddSchoolForm, AddSchoolsForm, EditSchoolForm
from view_handlers import handle_logged_in, handle_school_user
from view_handlers import handle_teacher_list, handle_student_list, handle_class_list


def logout_user(request):
    request.session.flush()
    return redirect('fitness_scoring.views.login_user')


def login_user(request):
    username = password = ''
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_type = authenticate(username=username, password=password)
        request.session['user_type'] = user_type   
        request.session['username'] = username
        if user_type == 'SuperUser':
            return redirect('fitness_scoring.views.superuser')
        elif user_type == 'Administrator':
            request.session['school_name'] = Administrator.objects.get(user=User.objects.get(username=username)).school_id.name
            return redirect('fitness_scoring.views.administrator')
        elif user_type == 'Teacher':
            teacher = Teacher.objects.get(user=User.objects.get(username=username))
            request.session['school_name'] = teacher.school_id.name
            request.session['teacher_full_name'] = teacher.first_name + " " + teacher.surname
            return redirect('fitness_scoring.views.teacher')
        elif user_type == 'Unpaid':
            state = "Subscription fee has not been paid for your school."
            return render(request, 'auth.html', RequestContext(request, {'state': state,
                                                                         'username': username}))
        else:
            state = "Incorrect username and/or password."
            return render(request, 'auth.html', RequestContext(request, {'state': state,
                                                                         'username': username}))
    else:
        state = ""
        return render(request, 'auth.html', RequestContext(request, {'state': state,
                                                                     'username': username}))


def authenticate(username, password):

    if len(User.objects.filter(username=username)) == 1:
        user = User.objects.get(username=username)
        superusers = SuperUser.objects.filter(user=user)
        administrators = Administrator.objects.filter(user=user)
        teachers = Teacher.objects.filter(user=user)
        if len(superusers) == 1:
            if check_password(password=password, encrypted_password=superusers[0].user.password):
                user_type = 'SuperUser'
            else:
                user_type = 'SuperUser Failed'
        elif len(administrators) == 1:
            if check_password(password=password, encrypted_password=administrators[0].user.password):
                if administrators[0].school_id.subscription_paid:
                    user_type = 'Administrator'
                else:
                    user_type = 'Unpaid'
            else:
                user_type = 'Administrator Failed'
        elif len(teachers) == 1:
            if check_password(password=password, encrypted_password=teachers[0].user.password):
                if teachers[0].school_id.subscription_paid:
                    user_type = 'Teacher'
                else:
                    user_type = 'Unpaid'
            else:
                user_type = 'Teacher Failed'

        else:
            user_type = 'Failed'
    else:
        user_type = 'Failed'

    return user_type


def check_password(password, encrypted_password):
    return password == encrypted_password


def teacher(request):
    if request.session.get('user_type', None) == 'Teacher':

        last_active_tab1 = 'student_list'

        context = {'user_type': 'Teacher',
                   'name': request.session.get('username', None),
                   'school_name': request.session.get('school_name', None),
                   'submit_to_page': '/teacher/'}

        if handle_student_list(request, context, csv_available=False):
            last_active_tab1 = 'student_list'

        context['last_active_tab'] = last_active_tab1

        return render(request, 'teacher.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def administrator(request):
    if request.session.get('user_type', None) == 'Administrator':

        context = {'submit_to_page': '/administrator/'}

        handle_logged_in(request, context)
        handle_school_user(request, context)

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


def superuser(request):
    if request.session.get('user_type', None) == 'SuperUser':

        context = {'submit_to_page': '/superuser/'}

        handle_logged_in(request, context)

        return render(request, 'superuser.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def school_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(school, school.get_display_items()) for school in School.objects.all()],
            'item_list_title': 'School List',
            'item_list_table_headings': School.get_display_list_headings(),
            'item_list_tab_id': 'school_list_tab',
            'item_list_url': '/school/list/',
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
                context = {'finish_title': 'School Added', 'finish_message': 'School Added Successfully: ' + school_add_form.cleaned_data['name']}
                return render(request, 'modal_finished_message.html', RequestContext(request, context))
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
                result_message = \
                    'Schools Created: '+str(n_created) + '\n' + \
                    'Schools Updated: '+str(n_updated) + '\n' + \
                    'No Changes From Data Lines: '+str(n_not_created_or_updated)
                context = {'finish_title': 'Schools Added/Updated', 'finish_message': result_message}
                return render(request, 'modal_finished_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/school/adds/', 'functionality_name': 'Add Schools', 'form': school_adds_form}
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
                           'finish_message': 'School Edited Successfully: ' + school_edit_form.cleaned_data['name']}
                return render(request, 'modal_finished_message.html', RequestContext(request, context))
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
                           'finish_message': 'School Deleted Successfully: ' + school_name}
            else:
                context = {'finish_title': 'School Not Deleted',
                           'finish_error_message': 'Could Not Delete ' + school_name + ' (School Being Used)'}
            return render(request, 'modal_finished_message.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/school/delete/' + str(school_pk),
                       'functionality_name': 'Delete School',
                       'prompt_message': 'Are You Sure You Wish To Delete ' + school_name + "?"}
            return render(request, 'modal_form.html', RequestContext(request, context))
    else:
        return HttpResponseForbidden("You are not authorised to delete a school")