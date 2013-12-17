from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from fitness_scoring.models import Teacher, Administrator, SuperUser, User, School


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
            teacher = Teacher.objects.get(user=username);
            request.session['school_name'] = teacher.school_id.name
            request.session['teacher_full_name'] = teacher.firstname + " " + teacher.surname
            return redirect('fitness_scoring.views.teacher')
        elif user_type == 'Unpaid':
            state = "Your school subscription has not been paid."
            return render(request, 'auth.html', RequestContext(request, {'state':state, 'username': username}))
        else:
            state = "Your username and/or password were incorrect."
            return render(request, 'auth.html', RequestContext(request, {'state':state, 'username': username}))
    else:
        state = ""
        return render(request, 'auth.html', RequestContext(request, {'state':state, 'username': username}))


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
            if(administrator[0].school_id.subscriptionPaid):
                user_type = 'Administrator'
            else:
                user_type = 'Unpaid'
        else:
            user_type = 'Administrator Failed'
    elif len(teacher) > 0:
        if check_password(password=password, encrypted_password=teacher[0].user.password):
            if(teacher[0].school_id.subscriptionPaid):
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
        return render(request, 'teacher.html', RequestContext(request, {'user_type':'Teacher','name':request.session.get('teacher_full_name', None),'school_name':request.session.get('school_name', None)}))
    else:
        return redirect('fitness_scoring.views.login_user')

def administrator(request):
    if request.session.get('user_type', None) == 'Administrator':
        return render(request, 'administrator.html', RequestContext(request, {'user_type':'Administrator','name':request.session.get('username', None),'school_name':request.session.get('school_name', None)}))
    else:
        return redirect('fitness_scoring.views.login_user')

def superuser(request):
    if request.session.get('user_type', None) == 'SuperUser':
        return render(request, 'superuser.html', RequestContext(request, {'user_type':'Super User','name':request.session.get('username', None),'school_list':School.objects.all()}))
    else:
        return redirect('fitness_scoring.views.login_user')

