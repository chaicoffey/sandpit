from django.shortcuts import render, redirect
from django.template import RequestContext
from django.contrib import messages
from fitness_scoring.models import Teacher, Administrator, SuperUser, User, Student, School, StudentClassEnrolment, TeacherClassAllocation
from fitness_scoring.models import create_student, create_teacher, get_school_name_max_length
from fitness_scoring.forms import AddStudentForm, AddStudentsForm, EditStudentForm, AddTeacherForm, AddTeachersForm, EditTeacherForm
from fileio import save_file, delete_file, add_students_from_file, add_teachers_from_file

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

        school_id = School.objects.get(name=request.session.get('school_name', None))

        (teacher_list_posted, add_teacher_form, add_teachers_form, edit_teacher_form, add_teacher_modal_visibility, add_teachers_modal_visibility, edit_teacher_modal_visibility) = teacher_list(request, school_id)
        (student_list_posted, add_student_form, add_students_form, edit_student_form, add_student_modal_visibility, add_students_modal_visibility, edit_student_modal_visibility) = student_list(request, school_id)

        return render(request, 'administrator.html',
                      RequestContext(request,
                                     {'user_type': 'Administrator',
                                      'name': request.session.get('username', None),
                                      'school_name': request.session.get('school_name', None),
                                      'submit_to_page': '/administrator/',
                                      'student_list': Student.objects.filter(school_id=school_id),
                                      'add_student_form': add_student_form,
                                      'add_students_form': add_students_form,
                                      'edit_student_form': edit_student_form,
                                      'add_student_modal_hide_or_show': add_student_modal_visibility,
                                      'add_students_modal_hide_or_show': add_students_modal_visibility,
                                      'edit_student_modal_hide_or_show': edit_student_modal_visibility,
                                      'teacher_list': Teacher.objects.filter(school_id=school_id),
                                      'add_teacher_form': add_teacher_form,
                                      'add_teachers_form': add_teachers_form,
                                      'edit_teacher_form': edit_teacher_form,
                                      'student_list_active': student_list_posted,
                                      'add_teacher_modal_hide_or_show': add_teacher_modal_visibility,
                                      'add_teachers_modal_hide_or_show': add_teachers_modal_visibility,
                                      'edit_teacher_modal_hide_or_show': edit_teacher_modal_visibility}))

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


def student_list(request, school_id):
    #This method goes with student_list.html (remember to include student_list_javascript.html in the appropriate place

    add_student_form = AddStudentForm()
    add_students_form = AddStudentsForm()
    edit_student_form = EditStudentForm()
    add_student_modal_visibility = 'hide'
    add_students_modal_visibility = 'hide'
    edit_student_modal_visibility = 'hide'
    student_list_posted = False
    if request.method == 'POST':
        if request.POST.get('SubmitIdentifier') == 'AddStudent':
            # If the form has been submitted
            student_list_posted = True
            add_student_form = AddStudentForm(request.POST)  # A form bound to the POST data
            if add_student_form.is_valid():
                student_id = add_student_form.cleaned_data['student_id']
                first_name = add_student_form.cleaned_data['first_name']
                surname = add_student_form.cleaned_data['surname']
                gender = add_student_form.cleaned_data['gender']
                dob = add_student_form.cleaned_data['dob']
                if create_student(check_name=False, student_id=student_id, school_id=school_id, first_name=first_name, surname=surname, gender=gender, dob=dob):
                    add_student_form = AddStudentForm()
                    messages.success(request, "Student Added: " + first_name + " " + surname + " (" + student_id + ")")
                else:
                    messages.success(request, "Error Adding Student: " + first_name + " " + surname + " (" + student_id + ") (Student ID Already Exists)")
            else:
                add_student_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'AddStudents':
            # If the form has been submitted
            student_list_posted = True
            add_students_form = AddStudentsForm(request.POST, request.FILES)  # A form bound to the POST data
            if add_students_form.is_valid():
                add_students_file = request.FILES['add_students_file']
                file_path_on_server = save_file(add_students_file)
                (n_created, n_updated, n_not_created_or_updated) = add_students_from_file(file_path_on_server, school_id)
                delete_file(file_path_on_server)
                messages.success(request, "Summary of changes made from .CSV: ")
                messages.success(request, "Students Created: "+str(n_created))
                messages.success(request, "Students Updated: "+str(n_updated))
                messages.success(request, "No Changes From Data Lines: "+str(n_not_created_or_updated))
            else:
                add_students_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'DeleteStudent':
            student_list_posted = True
            student_pk = request.POST.get('student_pk')
            student_to_delete = Student.objects.get(pk=student_pk)
            if len(StudentClassEnrolment.objects.filter(student_id=student_to_delete)) == 0:
                first_name = student_to_delete.first_name
                surname = student_to_delete.surname
                student_id = student_to_delete.student_id
                student_to_delete.delete()
                messages.success(request, "Student Deleted: " + first_name + " " + surname + " (" + student_id + ")")
            else:
                messages.success(request, "Error Deleting Student: " + student_to_delete.first_name + " " + student_to_delete.surname + " (" + student_to_delete.student_id + ") (Student Enrolled In Classes)")
        elif request.POST.get('SubmitIdentifier') == 'EditStudent':
            student_list_posted = True
            student_pk = request.POST.get('student_pk')
            student = Student.objects.get(pk=student_pk)
            request.session['edit_student_pk'] = student_pk
            edit_student_form = EditStudentForm(instance=student)
            edit_student_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'SaveStudent':
            student_list_posted = True
            edit_student_form = EditStudentForm(request.POST)
            if edit_student_form.is_valid():
                student_pk = request.session.get('edit_student_pk')
                student = Student.objects.get(pk=student_pk)
                edit_student_form = EditStudentForm(request.POST, instance=student)
                student_id_old = student.student_id
                student_id_new = request.POST.get('student_id')
                if (student_id_old == student_id_new) or (len(Student.objects.filter(school_id=school_id, student_id=student_id_new)) == 0):
                    edit_student_form.save()
                    messages.success(request, "Student Edited: " + student.first_name + " " + student.surname + " (" + student_id_old + ")")
                else:
                    messages.success(request, "Error Editing Student: " + student.first_name + " " + student.surname + " (" + student_id_old + ") (Student ID Already Exists: " + student_id_new + ")")
            else:
                edit_student_modal_visibility = 'show'

    return student_list_posted, add_student_form, add_students_form, edit_student_form, add_student_modal_visibility, add_students_modal_visibility, edit_student_modal_visibility


def teacher_list(request, school_id):
    #This method goes with teacher_list.html (remember to include teacher_list_javascript.html in the appropriate place

    add_teacher_form = AddTeacherForm()
    add_teachers_form = AddTeachersForm()
    edit_teacher_form = EditTeacherForm()
    add_teacher_modal_visibility = 'hide'
    add_teachers_modal_visibility = 'hide'
    edit_teacher_modal_visibility = 'hide'
    teacher_list_posted = False
    if request.method == 'POST':
        if request.POST.get('SubmitIdentifier') == 'AddTeacher':
            # If the form has been submitted
            teacher_list_posted = True
            add_teacher_form = AddTeacherForm(request.POST)  # A form bound to the POST data
            if add_teacher_form.is_valid():
                first_name = add_teacher_form.cleaned_data['first_name']
                surname = add_teacher_form.cleaned_data['surname']
                username = add_teacher_form.cleaned_data['username']
                password = add_teacher_form.cleaned_data['password']
                if create_teacher(check_name=False, first_name=first_name, surname=surname, school_id=school_id, username=username, password=password):
                    add_teacher_form = AddTeacherForm()
                    messages.success(request, "Teacher Added: " + first_name + " " + surname + " (" + username + ")")
                else:
                    messages.success(request, "Error Adding Teacher: " + first_name + " " + surname + " (" + username + ") (Username Already Exists)")
            else:
                add_teacher_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'AddTeachers':
            # If the form has been submitted
            teacher_list_posted = True
            add_teachers_form = AddTeachersForm(request.POST, request.FILES)  # A form bound to the POST data
            if add_teachers_form.is_valid():
                add_teachers_file = request.FILES['add_teachers_file']
                file_path_on_server = save_file(add_teachers_file)
                (n_created, n_updated, n_not_created_or_updated) = add_teachers_from_file(file_path_on_server, school_id)
                delete_file(file_path_on_server)
                messages.success(request, "Summary of changes made from .CSV: ")
                messages.success(request, "Teachers Created: "+str(n_created))
                messages.success(request, "Teachers Updated: "+str(n_updated))
                messages.success(request, "No Changes From Data Lines: "+str(n_not_created_or_updated))
            else:
                add_teachers_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'DeleteTeacher':
            teacher_list_posted = True
            teacher_pk = request.POST.get('teacher_pk')
            teacher_to_delete = Teacher.objects.get(pk=teacher_pk)
            if len(TeacherClassAllocation.objects.filter(teacher_id=teacher_to_delete)) == 0:
                first_name = teacher_to_delete.first_name
                surname = teacher_to_delete.surname
                username = teacher_to_delete.user.username
                teacher_to_delete.user.delete()
                teacher_to_delete.delete()
                messages.success(request, "Teacher Deleted: " + first_name + " " + surname + " (" + username + ")")
            else:
                messages.success(request, "Error Deleting Teacher: " + teacher_to_delete.first_name + " " + teacher_to_delete.surname + " (" + teacher_to_delete.user.username + ") (Teacher Has Classes)")
        elif request.POST.get('SubmitIdentifier') == 'EditTeacher':
            teacher_list_posted = True
            teacher_pk = request.POST.get('teacher_pk')
            teacher = Teacher.objects.get(pk=teacher_pk)
            request.session['edit_teacher_pk'] = teacher_pk
            edit_teacher_form = EditTeacherForm(initial={'first_name': teacher.first_name, 'surname': teacher.surname, 'username': teacher.user.username, 'password': teacher.user.password})
            edit_teacher_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'SaveTeacher':
            teacher_list_posted = True
            edit_teacher_form = EditTeacherForm(request.POST)
            if edit_teacher_form.is_valid():
                teacher_pk = request.session.get('edit_teacher_pk')
                teacher = Teacher.objects.get(pk=teacher_pk)
                teacher_username_old = teacher.user.username
                teacher_username_new = edit_teacher_form.cleaned_data['username']
                if (teacher_username_old == teacher_username_new) or (len(User.objects.filter(username=teacher_username_new)) == 0):
                    teacher.first_name = edit_teacher_form.cleaned_data['first_name']
                    teacher.surname = edit_teacher_form.cleaned_data['surname']
                    teacher.user.delete()
                    teacher.user = User.objects.create(username=teacher_username_new, password=edit_teacher_form.cleaned_data['password'])
                    teacher.save()
                    messages.success(request, "Teacher Edited: " + teacher.first_name + " " + teacher.surname + " (" + teacher_username_old + ")")
                else:
                    messages.success(request, "Error Editing Teacher: " + teacher.first_name + " " + teacher.surname + " (" + teacher_username_old + ") (Username Already Exists: " + teacher_username_new + ")")
            else:
                edit_teacher_modal_visibility = 'show'

    return teacher_list_posted, add_teacher_form, add_teachers_form, edit_teacher_form, add_teacher_modal_visibility, add_teachers_modal_visibility, edit_teacher_modal_visibility
