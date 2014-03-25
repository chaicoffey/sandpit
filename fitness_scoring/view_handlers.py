
from django.contrib import messages
from fitness_scoring.forms import AddTeacherForm, EditTeacherForm, AddStudentForm, EditStudentForm, AddClassForm, EditClassForm, AddSchoolForm, EditSchoolForm
from fitness_scoring.models import Teacher, Student, Class, School, Administrator, TeacherClassAllocation
from fileio import add_teachers_from_file_upload, add_students_from_file_upload, add_classes_from_file_upload, add_schools_from_file_upload


def handle_logged_in(request, context):
#This handler goes with loggedin.html
    context['user_type'] = request.session.get('user_type', None)
    context['name'] = request.session.get('username', None)


def handle_school_user(request, context):
#This handler goes with schooluser.html
    context['school_name'] = request.session.get('school_name', None)


def handle_teacher_list(request, context):
#This handler goes with teacher_list.html (remember to include teacher_list_javascript.html in the appropriate place)

    teacher_list_message_tag = "teacher_list"

    school_id = School.objects.get(name=request.session.get('school_name', None))

    def handle_post_add_teachers():
        handle_post = (request.POST.get('SubmitIdentifier') == 'AddTeachers')
        if handle_post:
            (n_created, n_updated, n_not_created_or_updated) = add_teachers_from_file_upload(request.FILES['add_teachers_file'], school_id)
            messages.success(request, "Summary of changes made from .CSV: ", extra_tags=teacher_list_message_tag)
            messages.success(request, "Teachers Created: "+str(n_created), extra_tags=teacher_list_message_tag)
            messages.success(request, "Teachers Updated: "+str(n_updated), extra_tags=teacher_list_message_tag)
            messages.success(request, "No Changes From Data Lines: "+str(n_not_created_or_updated), extra_tags=teacher_list_message_tag)
        return handle_post

    def handle_post_delete_teacher():
        handle_post = (request.POST.get('SubmitIdentifier') == 'DeleteTeacher')
        if handle_post:
            teacher_to_delete = Teacher.objects.get(pk=request.POST.get('teacher_pk'))
            teacher_string = teacher_to_delete.first_name + " " + teacher_to_delete.surname + " (" + teacher_to_delete.user.username + ")"
            if teacher_to_delete.delete_teacher_safe():
                messages.success(request, "Teacher Deleted: " + teacher_string, extra_tags=teacher_list_message_tag)
            else:
                messages.success(request, "Error Deleting Teacher: " + teacher_string + " (Teacher Has Classes)", extra_tags=teacher_list_message_tag)
        return handle_post

    context['teacher_list'] = Teacher.objects.filter(school_id=school_id)
    context['teacher_list_message_tag'] = teacher_list_message_tag
    context['add_teacher_form'] = AddTeacherForm()
    context['edit_teacher_form'] = EditTeacherForm()

    post_handled = False

    if request.method == 'POST':
        if not post_handled:
            post_handled = AddTeacherForm(request.POST).handle_posted_form(request=request, messages_tag=teacher_list_message_tag)
        if not post_handled:
            post_handled = EditTeacherForm(request.POST).handle_posted_form(request=request, messages_tag=teacher_list_message_tag)
        if not post_handled:
            post_handled = handle_post_add_teachers()
        if not post_handled:
            post_handled = handle_post_delete_teacher()

    return post_handled


def handle_student_list(request, context, csv_available=True):
#This handler goes with student_list.html (remember to include student_list_javascript.html in the appropriate place)

    student_list_message_tag = "student_list"

    school_id = School.objects.get(name=request.session.get('school_name', None))

    def handle_post_add_students():
        handle_post = (request.POST.get('SubmitIdentifier') == 'AddStudents')
        if handle_post:
            (n_created, n_updated, n_not_created_or_updated) = add_students_from_file_upload(request.FILES['add_students_file'], school_id)
            messages.success(request, "Summary of changes made from .CSV: ", extra_tags=student_list_message_tag)
            messages.success(request, "Students Created: "+str(n_created), extra_tags=student_list_message_tag)
            messages.success(request, "Students Updated: "+str(n_updated), extra_tags=student_list_message_tag)
            messages.success(request, "No Changes From Data Lines: "+str(n_not_created_or_updated), extra_tags=student_list_message_tag)
        return handle_post

    def handle_post_delete_student():
        handle_post = (request.POST.get('SubmitIdentifier') == 'DeleteStudent')
        if handle_post:
            student_to_delete = Student.objects.get(pk=request.POST.get('student_pk'))
            student_string = student_to_delete.first_name + " " + student_to_delete.surname + " (" + student_to_delete.student_id + ")"
            if student_to_delete.delete_student_safe():
                messages.success(request, "Student Deleted: " + student_string, extra_tags=student_list_message_tag)
            else:
                messages.success(request, "Error Deleting Student: " + student_string + " (Student Enrolled In Classes)", extra_tags=student_list_message_tag)
        return handle_post

    context['student_list'] = Student.objects.filter(school_id=school_id)
    context['student_list_message_tag'] = student_list_message_tag
    context['add_student_form'] = AddStudentForm()
    context['edit_student_form'] = EditStudentForm()
    context['csv_available'] = csv_available

    post_handled = False

    if request.method == 'POST':
        if not post_handled:
            post_handled = AddStudentForm(request.POST).handle_posted_form(request=request, messages_tag=student_list_message_tag)
        if not post_handled:
            post_handled = EditStudentForm(request.POST).handle_posted_form(request=request, messages_tag=student_list_message_tag)
        if not post_handled:
            post_handled = handle_post_add_students()
        if not post_handled:
            post_handled = handle_post_delete_student()

    return post_handled


def handle_class_list(request, context):
#This handler goes with class_list.html (remember to include class_list_javascript.html in the appropriate place)

    class_list_message_tag = "class_list"

    school_id = School.objects.get(name=request.session.get('school_name', None))

    def handle_post_add_classes():
        handle_post = (request.POST.get('SubmitIdentifier') == 'AddClasses')
        if handle_post:
            (n_created, n_updated, n_not_created_or_updated) = add_classes_from_file_upload(request.FILES['add_classes_file'], school_id)
            messages.success(request, "Summary of changes made from .CSV: ", extra_tags=class_list_message_tag)
            messages.success(request, "Classes Created: "+str(n_created), extra_tags=class_list_message_tag)
            messages.success(request, "Classes Updated: "+str(n_updated), extra_tags=class_list_message_tag)
            messages.success(request, "No Changes From Data Lines: "+str(n_not_created_or_updated), extra_tags=class_list_message_tag)
        return handle_post

    def handle_post_delete_class():
        handle_post = (request.POST.get('SubmitIdentifier') == 'DeleteClass')
        if handle_post:
            class_to_delete = Class.objects.get(pk=request.POST.get('class_pk'))
            class_string = class_to_delete.class_name + " (" + str(class_to_delete.year) + ")"
            if class_to_delete.delete_class_safe():
                messages.success(request, "Class Deleted: " + class_string, extra_tags=class_list_message_tag)
            else:
                messages.success(request, "Error Deleting Class: " + class_string + " (Class Enrolled In Classes)", extra_tags=class_list_message_tag)
        return handle_post

    post_handled = False

    if request.method == 'POST':
        if not post_handled:
            post_handled = AddClassForm(school_id, request.POST).handle_posted_form(request=request, messages_tag=class_list_message_tag)
        if not post_handled:
            post_handled = EditClassForm(school_id, request.POST).handle_posted_form(request=request, messages_tag=class_list_message_tag)
        if not post_handled:
            post_handled = handle_post_add_classes()
        if not post_handled:
            post_handled = handle_post_delete_class()

    class_list = Class.objects.filter(school_id=school_id)
    context['class_list'] = [(classInstance, TeacherClassAllocation.objects.get(class_id=classInstance).teacher_id) for classInstance in class_list]
    context['class_list_message_tag'] = class_list_message_tag
    context['add_class_form'] = AddClassForm(school_id=school_id)
    context['edit_class_form'] = EditClassForm(school_id=school_id)

    return post_handled


def handle_school_list(request, context):
#This handler goes with school_list.html (remember to include school_list_javascript.html in the appropriate place)

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

    context['administrator_list'] = Administrator.objects.all()
    context['school_list_message_tag'] = school_list_message_tag
    context['add_school_form'] = AddSchoolForm()
    context['edit_school_form'] = EditSchoolForm()

    post_handled = False

    if request.method == 'POST':
        if not post_handled:
            post_handled = AddSchoolForm(request.POST).handle_posted_form(request=request, messages_tag=school_list_message_tag)
        if not post_handled:
            post_handled = EditSchoolForm(request.POST).handle_posted_form(request=request, messages_tag=school_list_message_tag)
        if not post_handled:
            post_handled = handle_post_add_schools()
        if not post_handled:
            post_handled = handle_post_delete_school()

    return post_handled