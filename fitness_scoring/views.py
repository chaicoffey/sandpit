from django.shortcuts import render, redirect
from django.template import RequestContext
from django.contrib import messages
from fitness_scoring.models import Teacher, Administrator, SuperUser, School, Class, TeacherClassAllocation
from fitness_scoring.forms import AddClassForm, EditClassForm
from view_handlers import handle_logged_in, handle_teacher_list, handle_student_list, handle_school_list


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

        last_active_tab1 = 'teacher_list'

        school_id = School.objects.get(name=request.session.get('school_name', None))
        (add_class_form, add_classes_form, edit_class_form, add_class_modal_visibility, add_classes_modal_visibility, edit_class_modal_visibility) = class_list(request, school_id)

        context = {'user_type': 'Administrator',
                   'name': request.session.get('username', None),
                   'school_name': request.session.get('school_name', None),
                   'submit_to_page': '/administrator/',
                   'class_list': Class.objects.filter(school_id=school_id),
                   'add_class_form': add_class_form,
                   'add_classes_form': add_classes_form,
                   'edit_class_form': edit_class_form,
                   'add_class_modal_hide_or_show': add_class_modal_visibility,
                   'add_classes_modal_hide_or_show': add_classes_modal_visibility,
                   'edit_class_modal_hide_or_show': edit_class_modal_visibility}

        if handle_teacher_list(request, context):
            last_active_tab1 = 'teacher_list'
        elif handle_student_list(request, context):
            last_active_tab1 = 'student_list'

        context['last_active_tab'] = last_active_tab1

        return render(request, 'administrator.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


def superuser(request):
    if request.session.get('user_type', None) == 'SuperUser':

        context = {'submit_to_page': '/superuser/'}

        handle_logged_in(request, context)
        handle_school_list(request, context)

        return render(request, 'superuser.html', RequestContext(request, context))
    else:
        return redirect('fitness_scoring.views.login_user')


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


