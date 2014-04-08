from django.shortcuts import render, redirect, HttpResponse
from django.http import HttpResponseForbidden
from django.template import RequestContext
from fitness_scoring.models import User, Teacher, Administrator, SuperUser, School
from fitness_scoring.forms import AddSchoolForm
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
        return render(request, 'school_list.html', RequestContext(request, {'administrator_list': Administrator.objects.all()}))
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
                return render(request, 'school_add.html', RequestContext(request, {'school_add_form': school_add_form}))
        else:
            return render(request, 'school_add.html', RequestContext(request, {'school_add_form': AddSchoolForm()}))
    else:
        return HttpResponseForbidden("You are not authorised to add a school")


def school_adds(request):
    pass


def school_edit(request, school_pk):
    pass


def school_delete(request, school_pk):
    pass