from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from fitness_scoring.models import Teacher, Administrator, SuperUser, Student, User, School, get_school_name_max_length
from fitness_scoring.models import create_student
from fitness_scoring.forms import AddStudentForm, AddStudentsForm
from fileio import save_file, delete_file, add_students_from_file

# Create your views here.

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
            request.session['school_name'] = Administrator.objects.get(user=username).school_id.name
            return redirect('fitness_scoring.views.administrator')
        elif user_type == 'Teacher':
            teacher = Teacher.objects.get(user=username)
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
    superuser = SuperUser.objects.filter(user=username)
    administrator = Administrator.objects.filter(user=username)
    teacher = Teacher.objects.filter(user=username)
    if len(superuser) > 0:
        if check_password(password=password, encrypted_password=superuser[0].user.password):
            user_type = 'SuperUser'
        else:
            user_type = 'SuperUser Failed'
    elif len(administrator) > 0:
        if check_password(password=password, encrypted_password=administrator[0].user.password):
            if administrator[0].school_id.subscriptionPaid:
                user_type = 'Administrator'
            else:
                user_type = 'Unpaid'
        else:
            user_type = 'Administrator Failed'
    elif len(teacher) > 0:
        if check_password(password=password, encrypted_password=teacher[0].user.password):
            if teacher[0].school_id.subscriptionPaid:
                user_type = 'Teacher'
            else:
                user_type = 'Unpaid'
        else:
            user_type = 'Teacher Failed'
    else:
        user_type = 'Failed'

    return user_type


def check_password(password, encrypted_password):
    return password == encrypted_password


def teacher(request):
    if request.session.get('user_type', None) == 'Teacher':
        return render(request, 'teacher.html',
                      RequestContext(request,
                                     {'user_type': 'Teacher',
                                      'name': request.session.get('teacher_full_name', None),
                                      'school_name': request.session.get('school_name', None)}))
    else:
        return redirect('fitness_scoring.views.login_user')


def administrator(request):
    if request.session.get('user_type', None) == 'Administrator':
        add_student_form = AddStudentForm()
        add_students_form = AddStudentsForm()
        school_id = School.objects.get(name=request.session.get('school_name', None))
        add_student_modal_visibility = 'hide'
        add_students_modal_visibility = 'hide'
        if request.method == 'POST':
            if request.POST.get('SubmitIdentifier') == 'AddStudent':
                # If the form has been submitted
                add_student_form = AddStudentForm(request.POST)  # A form bound to the POST data
                if add_student_form.is_valid():
                    student_id = add_student_form.cleaned_data['student_id']
                    first_name = add_student_form.cleaned_data['first_name']
                    surname = add_student_form.cleaned_data['surname']
                    gender = add_student_form.cleaned_data['gender']
                    dob = add_student_form.cleaned_data['dob']
                    if(create_student(check_name=False, student_id=student_id, school_id=school_id, first_name=first_name, surname=surname, gender=gender, dob=dob)):
                        return redirect('/administrator/')  # Redirect after POST
                    else:
                        add_student_modal_visibility = 'show'
                else:
                    add_student_modal_visibility = 'show'
            elif request.POST.get('SubmitIdentifier') == 'AddStudents':
                # If the form has been submitted
                add_students_form = AddStudentsForm(request.POST, request.FILES)  # A form bound to the POST data
                if add_students_form.is_valid():
                    add_students_file = request.FILES['add_students_file']
                    file_path_on_server = save_file(add_students_file)
                    (n_created, n_updated, n_not_created_or_updated) = add_students_from_file(file_path_on_server, school_id)
                    delete_file(file_path_on_server)
                    return redirect('/administrator/')  # Redirect after POST
                else:
                    add_students_modal_visibility = 'show'
        return render(request, 'administrator.html',
                      RequestContext(request,
                                     {'user_type': 'Administrator',
                                      'name': request.session.get('username', None),
                                      'school_name': request.session.get('school_name', None),
                                      'student_list': Student.objects.filter(school_id=school_id),
                                      'add_student_form': add_student_form,
                                      'add_students_form': add_students_form,
                                      'add_student_modal_hide_or_show': add_student_modal_visibility,
                                      'add_students_modal_hide_or_show': add_students_modal_visibility}))
    else:
        return redirect('fitness_scoring.views.login_user')


def superuser(request):
    if request.session.get('user_type', None) == 'SuperUser':
        school_name_max_length = get_school_name_max_length()
        return render(request, 'superuser.html',
                      RequestContext(request,
                                     {'user_type': 'Super User',
                                      'name': request.session.get('username', None),
                                      'school_list': [(school.get_school_name_padded(school_name_max_length), school.get_subscription_paid_text()) for school in School.objects.all()]
                                      }))
    else:
        return redirect('fitness_scoring.views.login_user')


