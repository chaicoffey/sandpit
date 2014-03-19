from django.shortcuts import render, redirect
from django.template import RequestContext
from django.contrib import messages
from fitness_scoring.models import Teacher, Administrator, SuperUser, User, Student, School, Class, \
    StudentClassEnrolment, TeacherClassAllocation
from fitness_scoring.models import create_student, create_teacher
from fitness_scoring.forms import AddStudentForm, AddStudentsForm, EditStudentForm
from fitness_scoring.forms import AddTeacherForm, AddTeachersForm, EditTeacherForm
from fitness_scoring.forms import AddClassForm, EditClassForm
from fitness_scoring.forms import AddSchoolForm, EditSchoolForm
from fileio import save_file, delete_file, add_students_from_file, add_teachers_from_file, add_schools_from_file_upload


# Create your views here.
last_active_tab = 'teacher_list'  # This is a hack and should be fixed.


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
            if administrator[0].school_id.subscription_paid:
                user_type = 'Administrator'
            else:
                user_type = 'Unpaid'
        else:
            user_type = 'Administrator Failed'
    elif len(teacher) > 0:
        if check_password(password=password, encrypted_password=teacher[0].user.password):
            if teacher[0].school_id.subscription_paid:
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

        (add_teacher_form, add_teachers_form, edit_teacher_form, add_teacher_modal_visibility, add_teachers_modal_visibility, edit_teacher_modal_visibility) = teacher_list(request, school_id)
        (add_student_form, add_students_form, edit_student_form, add_student_modal_visibility, add_students_modal_visibility, edit_student_modal_visibility) = student_list(request, school_id)
        (add_class_form, add_classes_form, edit_class_form, add_class_modal_visibility, add_classes_modal_visibility, edit_class_modal_visibility) = class_list(request, school_id)

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
                                      'last_active_tab': last_active_tab,
                                      'add_teacher_modal_hide_or_show': add_teacher_modal_visibility,
                                      'add_teachers_modal_hide_or_show': add_teachers_modal_visibility,
                                      'edit_teacher_modal_hide_or_show': edit_teacher_modal_visibility,
                                      'class_list': Class.objects.filter(school_id=school_id),
                                      'add_class_form': add_class_form,
                                      'add_classes_form': add_classes_form,
                                      'edit_class_form': edit_class_form,
                                      'add_class_modal_hide_or_show': add_class_modal_visibility,
                                      'add_classes_modal_hide_or_show': add_classes_modal_visibility,
                                      'edit_class_modal_hide_or_show': edit_class_modal_visibility}))

    else:
        return redirect('fitness_scoring.views.login_user')


def superuser(request):
    if request.session.get('user_type', None) == 'SuperUser':

        if request.method == 'POST':
            handle_post_school_list(request)

        return render(request, 'superuser.html',
                      RequestContext(request,
                                     {'user_type': 'Super User',
                                      'name': request.session.get('username', None),
                                      'submit_to_page': '/superuser/',
                                      'administrator_list': Administrator.objects.all(),
                                      'add_school_form': AddSchoolForm(),
                                      'edit_school_form': EditSchoolForm()
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
    global last_active_tab
    if request.method == 'POST':
        if request.POST.get('SubmitIdentifier') == 'AddStudent':
            # If the form has been submitted
            last_active_tab = 'student_list'
            add_student_form = AddStudentForm(request.POST)  # A form bound to the POST data
            if add_student_form.is_valid():
                student_id = add_student_form.cleaned_data['student_id']
                first_name = add_student_form.cleaned_data['first_name']
                surname = add_student_form.cleaned_data['surname']
                gender = add_student_form.cleaned_data['gender']
                dob = add_student_form.cleaned_data['dob']
                if create_student(check_name=False, student_id=student_id, school_id=school_id, first_name=first_name, surname=surname, gender=gender, dob=dob):
                    add_student_form = AddStudentForm()
                    messages.success(request, "Student Added: " + first_name + " " + surname + " (" + student_id + ")", extra_tags="student_list")
                else:
                    messages.success(request, "Error Adding Student: " + first_name + " " + surname + " (" + student_id + ") (Student ID Already Exists)", extra_tags="student_list")
            else:
                add_student_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'AddStudents':
            # If the form has been submitted
            last_active_tab = 'student_list'
            add_students_form = AddStudentsForm(request.POST, request.FILES)  # A form bound to the POST data
            if add_students_form.is_valid():
                add_students_file = request.FILES['add_students_file']
                file_path_on_server = save_file(add_students_file)
                (n_created, n_updated, n_not_created_or_updated) = add_students_from_file(file_path_on_server, school_id)
                delete_file(file_path_on_server)
                messages.success(request, "Summary of changes made from .CSV: ", extra_tags="student_list")
                messages.success(request, "Students Created: "+str(n_created), extra_tags="student_list")
                messages.success(request, "Students Updated: "+str(n_updated), extra_tags="student_list")
                messages.success(request, "No Changes From Data Lines: "+str(n_not_created_or_updated), extra_tags="student_list")
            else:
                add_students_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'DeleteStudent':
            last_active_tab = 'student_list'
            student_pk = request.POST.get('student_pk')
            student_to_delete = Student.objects.get(pk=student_pk)
            if len(StudentClassEnrolment.objects.filter(student_id=student_to_delete)) == 0:
                first_name = student_to_delete.first_name
                surname = student_to_delete.surname
                student_id = student_to_delete.student_id
                student_to_delete.delete()
                messages.success(request, "Student Deleted: " + first_name + " " + surname + " (" + student_id + ")", extra_tags="student_list")
            else:
                messages.success(request, "Error Deleting Student: " + student_to_delete.first_name + " " + student_to_delete.surname + " (" + student_to_delete.student_id + ") (Student Enrolled In Classes)", extra_tags="student_list")
        elif request.POST.get('SubmitIdentifier') == 'EditStudent':
            last_active_tab = 'student_list'
            student_pk = request.POST.get('student_pk')
            student = Student.objects.get(pk=student_pk)
            request.session['edit_student_pk'] = student_pk
            edit_student_form = EditStudentForm(instance=student)
            edit_student_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'SaveStudent':
            last_active_tab = 'student_list'
            edit_student_form = EditStudentForm(request.POST)
            if edit_student_form.is_valid():
                student_pk = request.session.get('edit_student_pk')
                student = Student.objects.get(pk=student_pk)
                edit_student_form = EditStudentForm(request.POST, instance=student)
                student_id_old = student.student_id
                student_id_new = request.POST.get('student_id')
                if (student_id_old == student_id_new) or (len(Student.objects.filter(school_id=school_id, student_id=student_id_new)) == 0):
                    edit_student_form.save()
                    messages.success(request, "Student Edited: " + student.first_name + " " + student.surname + " (" + student_id_old + ")", extra_tags="student_list")
                else:
                    messages.success(request, "Error Editing Student: " + student.first_name + " " + student.surname + " (" + student_id_old + ") (Student ID Already Exists: " + student_id_new + ")", extra_tags="student_list")
            else:
                edit_student_modal_visibility = 'show'

    return add_student_form, add_students_form, edit_student_form, add_student_modal_visibility, add_students_modal_visibility, edit_student_modal_visibility


def teacher_list(request, school_id):
    #This method goes with teacher_list.html (remember to include teacher_list_javascript.html in the appropriate place

    add_teacher_form = AddTeacherForm()
    add_teachers_form = AddTeachersForm()
    edit_teacher_form = EditTeacherForm()
    add_teacher_modal_visibility = 'hide'
    add_teachers_modal_visibility = 'hide'
    edit_teacher_modal_visibility = 'hide'
    global last_active_tab
    if request.method == 'POST':
        if request.POST.get('SubmitIdentifier') == 'AddTeacher':
            # If the form has been submitted
            last_active_tab = 'teacher_list'
            add_teacher_form = AddTeacherForm(request.POST)  # A form bound to the POST data
            if add_teacher_form.is_valid():
                first_name = add_teacher_form.cleaned_data['first_name']
                surname = add_teacher_form.cleaned_data['surname']
                username = add_teacher_form.cleaned_data['username']
                password = add_teacher_form.cleaned_data['password']
                if create_teacher(check_name=False, first_name=first_name, surname=surname, school_id=school_id, username=username, password=password):
                    add_teacher_form = AddTeacherForm()
                    messages.success(request, "Teacher Added: " + first_name + " " + surname + " (" + username + ")", extra_tags="teacher_list")
                else:
                    messages.success(request, "Error Adding Teacher: " + first_name + " " + surname + " (" + username + ") (Username Already Exists)", extra_tags="teacher_list")
            else:
                add_teacher_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'AddTeachers':
            # If the form has been submitted
            last_active_tab = 'teacher_list'
            add_teachers_form = AddTeachersForm(request.POST, request.FILES)  # A form bound to the POST data
            if add_teachers_form.is_valid():
                add_teachers_file = request.FILES['add_teachers_file']
                file_path_on_server = save_file(add_teachers_file)
                (n_created, n_updated, n_not_created_or_updated) = add_teachers_from_file(file_path_on_server, school_id)
                delete_file(file_path_on_server)
                messages.success(request, "Summary of changes made from .CSV: ", extra_tags="teacher_list")
                messages.success(request, "Teachers Created: "+str(n_created), extra_tags="teacher_list")
                messages.success(request, "Teachers Updated: "+str(n_updated), extra_tags="teacher_list")
                messages.success(request, "No Changes From Data Lines: "+str(n_not_created_or_updated), extra_tags="teacher_list")
            else:
                add_teachers_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'DeleteTeacher':
            last_active_tab = 'teacher_list'
            teacher_pk = request.POST.get('teacher_pk')
            teacher_to_delete = Teacher.objects.get(pk=teacher_pk)
            if len(TeacherClassAllocation.objects.filter(teacher_id=teacher_to_delete)) == 0:
                first_name = teacher_to_delete.first_name
                surname = teacher_to_delete.surname
                username = teacher_to_delete.user.username
                teacher_to_delete.user.delete()
                teacher_to_delete.delete()
                messages.success(request, "Teacher Deleted: " + first_name + " " + surname + " (" + username + ")", extra_tags="teacher_list")
            else:
                messages.success(request, "Error Deleting Teacher: " + teacher_to_delete.first_name + " " + teacher_to_delete.surname + " (" + teacher_to_delete.user.username + ") (Teacher Has Classes)", extra_tags="teacher_list")
        elif request.POST.get('SubmitIdentifier') == 'EditTeacher':
            last_active_tab = 'teacher_list'
            teacher_pk = request.POST.get('teacher_pk')
            teacher = Teacher.objects.get(pk=teacher_pk)
            request.session['edit_teacher_pk'] = teacher_pk
            edit_teacher_form = EditTeacherForm(initial={'first_name': teacher.first_name, 'surname': teacher.surname, 'username': teacher.user.username, 'password': teacher.user.password})
            edit_teacher_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'SaveTeacher':
            last_active_tab = 'teacher_list'
            edit_teacher_form = EditTeacherForm(request.POST)
            if edit_teacher_form.is_valid():
                teacher_pk = request.session.get('edit_teacher_pk')
                teacher = Teacher.objects.get(pk=teacher_pk)
                teacher_username_old = teacher.user.username
                teacher_username_new = edit_teacher_form.cleaned_data['username']
                if (teacher_username_old == teacher_username_new) or \
                        (len(User.objects.filter(username=teacher_username_new)) == 0):
                    teacher.first_name = edit_teacher_form.cleaned_data['first_name']
                    teacher.surname = edit_teacher_form.cleaned_data['surname']
                    teacher.user.delete()
                    teacher.user = User.objects.create(username=teacher_username_new,
                                                       password=edit_teacher_form.cleaned_data['password'])
                    teacher.save()
                    messages.success(request, "Teacher Edited: "
                                              + teacher.first_name + " "
                                              + teacher.surname + " (" + teacher_username_old + ")",
                                     extra_tags="teacher_list")
                else:
                    messages.success(request, "Error Editing Teacher: " + teacher.first_name + " " + teacher.surname + " (" + teacher_username_old + ") (Username Already Exists: " + teacher_username_new + ")", extra_tags="teacher_list")
            else:
                edit_teacher_modal_visibility = 'show'

    return add_teacher_form, add_teachers_form, edit_teacher_form, add_teacher_modal_visibility, add_teachers_modal_visibility, edit_teacher_modal_visibility


def class_list(request, school_id):
    #This method goes with class_list.html (remember to include class_list_javascript.html in the appropriate place

    add_class_form = AddClassForm(school_id=school_id)
    add_classes_form = AddClassForm() #AddClassesForm()
    edit_class_form = EditClassForm(school_id=school_id)
    add_class_modal_visibility = 'hide'
    add_classes_modal_visibility = 'hide'
    edit_class_modal_visibility = 'hide'
    global last_active_tab
    if request.method == 'POST':
        if request.POST.get('SubmitIdentifier') == 'AddClass':
            # If the form has been submitted
            last_active_tab = 'class_list'
            #new_class = Class(school_id=school_id)
            add_class_form = AddClassForm(request.POST, school_id=school_id)#, instance=new_class)  # A form bound to the POST data
            if add_class_form.is_valid():
                new_class = add_class_form.save(commit=False)
                new_class.school_id = school_id
                new_class.save()
                for teacher in add_class_form.cleaned_data.get('teachers'):
                    teacher_class_allocation = TeacherClassAllocation(teacher_id=teacher, class_id=new_class)
                    teacher_class_allocation.save()
                #class_id = add_class_form.cleaned_data['class_id']
                #if create_class(check_name=False, class_id=class_id, school_id=school_id, first_name=first_name, surname=surname, gender=gender, dob=dob):
                #    add_class_form = AddClassForm()
                messages.success(request, "Class Added.", extra_tags="class_list")
                #else:
                #    messages.success(request, "Error Adding Class: " + first_name + " " + surname + " (" + class_id + ") (Class ID Already Exists)", extra_tags="class_list")
            else:
                add_class_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'AddClasses':
            # If the form has been submitted
            last_active_tab = 'class_list'
            #add_classes_form = AddClassesForm(request.POST, request.FILES)  # A form bound to the POST data
            #if add_classes_form.is_valid():
            #    add_classes_file = request.FILES['add_classes_file']
            #    file_path_on_server = save_file(add_classes_file)
            #    (n_created, n_updated, n_not_created_or_updated) = add_classes_from_file(file_path_on_server, school_id)
            #    delete_file(file_path_on_server)
            #    messages.success(request, "Summary of changes made from .CSV: ", extra_tags="class_list")
            #    messages.success(request, "Classes Created: "+str(n_created), extra_tags="class_list")
            #    messages.success(request, "Classes Updated: "+str(n_updated), extra_tags="class_list")
            #    messages.success(request, "No Changes From Data Lines: "+str(n_not_created_or_updated), extra_tags="class_list")
            #else:
            #    add_classes_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'DeleteClass':
            last_active_tab = 'class_list'
            class_pk = request.POST.get('class_pk')
            class_to_delete = Class.objects.get(pk=class_pk)
            #if len(ClassClassEnrolment.objects.filter(class_id=class_to_delete)) == 0:
            #    first_name = class_to_delete.first_name
            #    surname = class_to_delete.surname
            #    class_id = class_to_delete.class_id
            class_to_delete.delete()
            #    messages.success(request, "Class Deleted: " + first_name + " " + surname + " (" + class_id + ")", extra_tags="class_list")
            #else:
            #    messages.success(request, "Error Deleting Class: " + class_to_delete.first_name + " " + class_to_delete.surname + " (" + class_to_delete.class_id + ") (Class Enrolled In Classes)", extra_tags="class_list")
        elif request.POST.get('SubmitIdentifier') == 'EditClass':
            messages.success(request, "Test message", extra_tags='class_list')
            last_active_tab = 'class_list'
            class_pk = request.POST.get('class_pk')
            peclass = Class.objects.get(pk=class_pk)
            request.session['edit_class_pk'] = class_pk
            edit_class_form = EditClassForm(instance=peclass, school_id=school_id)
            edit_class_modal_visibility = 'show'
        elif request.POST.get('SubmitIdentifier') == 'SaveClass':
            last_active_tab = 'class_list'
            edit_class_form = EditClassForm(request.POST, school_id=school_id)
            if edit_class_form.is_valid():
                class_pk = request.session.get('edit_class_pk')
                peclass = Class.objects.get(pk=class_pk)
                edit_class_form = EditClassForm(request.POST, instance=peclass)
            #    class_id_old = class.class_id
            #    class_id_new = request.POST.get('class_id')
            #    if (class_id_old == class_id_new) or (len(Class.objects.filter(school_id=school_id, class_id=class_id_new)) == 0):
            #        edit_class_form.save()
            #        messages.success(request, "Class Edited: " + class.first_name + " " + class.surname + " (" + class_id_old + ")", extra_tags="class_list")
            #    else:
            #        messages.success(request, "Error Editing Class: " + class.first_name + " " + class.surname + " (" + class_id_old + ") (Class ID Already Exists: " + class_id_new + ")", extra_tags="class_list")
                peclass = edit_class_form.save(commit=False)
                peclass.school_id = school_id
                peclass.save()
                for classallocation in TeacherClassAllocation.objects.filter(class_id=peclass):
                    classallocation.delete()
                for teacher in edit_class_form.cleaned_data.get('teachers'):
                    teacher_class_allocation = TeacherClassAllocation(teacher_id=teacher, class_id=peclass)
                    teacher_class_allocation.save()
            else:
                edit_class_modal_visibility = 'show'

    return add_class_form, add_classes_form, edit_class_form, add_class_modal_visibility, add_classes_modal_visibility, edit_class_modal_visibility


def handle_post_school_list(request):

    school_list_message_tag = "school_list"

    def handle_post_add_schools():
        handle_post = (request.POST.get('SubmitIdentifier') == 'AddSchools')
        if handle_post:
            (n_created, n_updated, n_not_created_or_updated) = add_schools_from_file_upload(request.FILES['add_schools_file'])
            messages.success(request, "Summary of changes made from .CSV: ", extra_tags=school_list_message_tag)
            messages.success(request, "Schools Created: "+str(n_created), extra_tags=school_list_message_tag)
            messages.success(request, "Schools Updated: "+str(n_updated), extra_tags=school_list_message_tag)
            messages.success(request, "No Changes From Data Lines: "+str(n_not_created_or_updated), extra_tags=school_list_message_tag)
        return handle_post

    def handle_post_delete_school():
        handle_post = (request.POST.get('SubmitIdentifier') == 'DeleteSchool')
        if handle_post:
            school_to_delete = School.objects.get(pk=request.POST.get('school_pk'))
            school_name = school_to_delete.name
            if school_to_delete.delete_school_safe():
                messages.success(request, "School Deleted: " + school_name, extra_tags=school_list_message_tag)
            else:
                messages.success(request, "Error Deleting School: " + school_to_delete.name + " (School is being used)", extra_tags=school_list_message_tag)
        return handle_post

    post_handled = False

    if not post_handled:
        post_handled = AddSchoolForm(request.POST).handle_posted_form(request=request, messages_tag=school_list_message_tag)
    if not post_handled:
        post_handled = EditSchoolForm(request.POST).handle_posted_form(request=request, messages_tag=school_list_message_tag)
    if not post_handled:
        post_handled = handle_post_add_schools()
    if not post_handled:
        post_handled = handle_post_delete_school()

    return post_handled