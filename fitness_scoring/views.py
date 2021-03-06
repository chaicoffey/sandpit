from django.shortcuts import render, redirect
from django.template import RequestContext
from fitness_scoring.models import User, Teacher, Administrator, SuperUser, School, Class
from fitness_scoring.models import TestCategory, MajorTestCategory, Test, PercentileBracketList
from fitness_scoring.models import TeacherClassAllocation, ClassTest, StudentClassEnrolment
from fitness_scoring.models import StudentClassTestResult
from fitness_scoring.forms import ChangePasswordFrom
from fitness_scoring.forms import AddSchoolForm, AddSchoolsForm, EditSchoolForm
from fitness_scoring.forms import AddTestCategoryForm, AddTestCategoriesForm, EditTestCategoryForm
from fitness_scoring.forms import AddMajorTestCategoryForm, AddMajorTestCategoriesForm, EditMajorTestCategoryForm
from fitness_scoring.forms import AddTestsForm, EditTestForm, UpdateTestFromFileForm
from fitness_scoring.forms import AddTeacherForm, EditTeacherForm
from fitness_scoring.forms import AddClassForm, AddClassesForm, EditClassForm, AddClassTeacherForm, EditClassTeacherForm
from fitness_scoring.forms import AllocateEditTestsToClassForm, AllocateEditDefaultTestsForm, AllocateTestsToClassForm
from fitness_scoring.forms import ResolveIssuesPersonalForm, ResolveIssuesClassForm
from fitness_scoring.forms import ResolveIssuesSchoolIDForm, ResolveIssuesSchoolNameForm, ResolveIssuesForm
from fitness_scoring.forms import StudentEntryForm, StudentEntryEditForm
from fitness_scoring.user_emails import send_email_user_reset, web_address
from operator import itemgetter


def login_user(request):

    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = User.get_authenticated_user(username=username, password=password)
        if user:
            if SuperUser.objects.filter(user=user).exists():
                user_type = 'Licencing'
            elif Administrator.objects.filter(user=user).exists():
                if Administrator.objects.get(user=user).school_id.subscription_paid:
                    user_type = 'Licencing'
                else:
                    user_type = 'Unpaid'
            elif Teacher.objects.filter(user=user).exists():
                if Teacher.objects.get(user=user).school_id.subscription_paid:
                    user_type = 'Licencing'
                else:
                    user_type = 'Unpaid'
            elif Class.objects.filter(user=user).exists():
                if Class.objects.get(user=user).school_id.subscription_paid:
                    user_type = 'Licencing'
                else:
                    user_type = 'Unpaid'
            else:
                user_type = "Unrecognised User Type"
        else:
            user_type = "Authentication Failed"

        request.session['user_type'] = user_type   
        request.session['username'] = username

        if user_type == 'Licencing':
            return redirect('fitness_scoring.views.licencing_check')
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


def licencing_check(request):
    user_type = request.session.get('user_type', None)
    if user_type == 'Licencing':
        user = User.objects.get(username=request.session.get('username'))
        if request.POST:
            if 'agree_button' in request.POST.keys():
                user.set_read_agreement()
                return redirect('fitness_scoring.views.licencing_check')
            else:
                return redirect('fitness_scoring.views.login_user')
        else:
            if user.read_agreement:
                if SuperUser.objects.filter(user=user).exists():
                    request.session['user_type'] = 'SuperUser'
                    return redirect('fitness_scoring.views.superuser_view')
                elif Administrator.objects.filter(user=user).exists():
                    request.session['user_type'] = 'Administrator'
                    return redirect('fitness_scoring.views.administrator_view')
                elif Teacher.objects.filter(user=user).exists():
                    request.session['user_type'] = 'Teacher'
                    return redirect('fitness_scoring.views.teacher_view')
                elif Class.objects.filter(user=user).exists():
                    request.session['user_type'] = 'Class'
                    return redirect('fitness_scoring.views.class_student_view')
                else:
                    return reload_window_to_login(request)
            else:
                return render(request, 'licencing_agreement.html', RequestContext(request,
                                                                                  {'post_to_url': '/licencing_check/'}))
    else:
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
                enrolment = form.save_student_entry()
                if enrolment:
                    return redirect('fitness_scoring.views.class_student_results_view', enrolment_pk=enrolment.pk)
                else:
                    context['form'] = form
                    return render(request, 'student_entry_form.html', RequestContext(request, context))
        else:
            context['form'] = StudentEntryForm(class_pk=class_instance.pk)
            return render(request, 'student_entry_form.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def class_student_results_view(request, enrolment_pk):
    if request.session.get('user_type', None) == 'Class':
        class_instance = Class.objects.get(user=User.objects.get(username=request.session.get('username', None)))
        enrolment = StudentClassEnrolment.objects.get(pk=enrolment_pk)
        if enrolment.class_id == class_instance:

            results_dictionary = {}
            for result in StudentClassTestResult.objects.filter(student_class_enrolment=enrolment):
                major_category_name = result.test.major_test_category.major_test_category_name
                category_name = result.test.test_category.test_category_name
                if not major_category_name in results_dictionary:
                    results_dictionary[major_category_name] = {}
                if not category_name in results_dictionary[major_category_name]:
                    results_dictionary[major_category_name][category_name] = []
                unit = result.test.percentiles.get_result_unit_text()
                unit = "" if unit == "" else " " + unit
                if result.percentile:
                    percentile = result.percentile
                    converted_percentile = result.get_converted_percentile()
                else:
                    percentile = 0
                    converted_percentile = 0
                results_dictionary[major_category_name][category_name].append((result.test.test_name,
                                                                               result.result + unit,
                                                                               percentile,
                                                                               converted_percentile))

            all_results = []
            overall_total = 0.0
            overall_count = 0
            for major_category_name in results_dictionary.keys():
                major_category_results = []
                major_category_total = 0.0
                major_category_count = 0
                count = 0
                for category_name in results_dictionary[major_category_name].keys():
                    category_results = []
                    category_total = 0
                    category_count = 0
                    for (test_name, score, percentile,
                         converted_percentile) in results_dictionary[major_category_name][category_name]:
                        category_results.append((count, test_name.replace(" ", "_"), test_name, score, percentile))
                        category_total += converted_percentile
                        category_count += 1
                        count += 1
                    category_score = float(category_total)/float(category_count)
                    major_category_total += category_score
                    major_category_count += 1
                    major_category_results.append((category_name.replace(" ", "_"), category_name, category_results))
                major_category_score = major_category_total/float(major_category_count)
                overall_total += major_category_score
                overall_count += 1
                all_results.append((major_category_name.replace(" ", "_"), major_category_name,
                                    int(round(major_category_score)), major_category_results))
            overall_score = overall_total/float(overall_count)

            context = {'post_to_url': '/logout/',
                       'student_name': enrolment.student_id,
                       'gender': enrolment.student_gender_at_time_of_enrolment,
                       'age': enrolment.get_student_age_at_time_of_enrolment(),
                       'results': all_results,
                       'overall_score': int(round(overall_score))}
            return render(request, 'class_student_results.html', RequestContext(request, context))

        else:
            return reload_window_to_login(request)
    else:
        return reload_window_to_login(request)


def teacher_view(request):
    if request.session.get('user_type', None) == 'Teacher':

        teacher = Teacher.objects.get(user=User.objects.get(username=request.session.get('username')))
        heading = teacher.first_name + ' ' + teacher.surname + ' (' + teacher.school_id.name + ')'

        steps = [
            ('Add Classes For Term', 'Classes_Link', 'teacher_add_classes',
             "Follow the diagrams to add all of your classes for the term.  "
             " **This step may have already been done by the administrator for you**.  "
             "When you're done click the <div class='arrow-right' style='display: inline-block'></div> above to see "
             "the next step.",
             [
                 ('teacher_add_classes_B.png', None), ('teacher_add_classes_D.png', None)
             ]),
            ('Print Test Instructions', 'Classes_Link', 'teacher_print_instructions',
             "Follow the diagrams to print the test instructions.  Do this for each class however if two classes "
             "have the same set of tests you only need to do it for one of them.",
             [
                 ('print_instructions_C.png', None), ('print_instructions_D.png', None)
             ]),
            ('Print Results Entry Sheet', 'Classes_Link', 'teacher_print_results_entry',
             "Follow the diagrams to print the student results entry sheets.  The students will use these to write "
             "down their results. Make sure you print off enough copies for all the students in the class.  Do this "
             "for each class.",
             [
                 ('print_results_entry_C.png', None), ('print_instructions_D.png', None)
             ]),
            ('Run Tests', 'Classes_Link', None,
             "Use the printed instructions to run the tests with the students in each class.  Make sure they record "
             "the results.  After you have done this return to the program and see the next step for getting the "
             "students to enter the results.",
             None),
            ('Get Class Login Details', 'Classes_Link', 'teacher_get_login_details',
             "You must now obtain a username and password for each class for the students to login and enter their "
             "results with.  Write down the login details that are displayed for each class.",
             [
                 ('get_login_C.png', None), ('get_login_D.png', 'NOTE DETAILS'), ('teacher_add_classes_D.png', None)
             ]),
            ('Get Students To Enter Results', 'Classes_Link', 'student_enter_results',
             "Get all students to sign into this site with the class login details obtained in the previous step.  "
             "Then they can enter their results.  The site address is " + web_address,
             [
                 ('enter_results_A.png', None), ('enter_results_B.png', None)
             ]),
            ('Approve Entries For Class', 'Classes_Link', 'teacher_approve_entries',
             "For each class go to the class home page.  If a student has entered information the system believes is "
             "incorrect you will see a <span class='glyphicon glyphicon-exclamation-sign attention_color'></span> "
             "next to the student name.  If you see this symbol click it to resolve the problem.  Once all pending "
             "issues are resolved check over each student's results and if you think they are correct tick the box to "
             "approve them.  Make sure to do this for all of your classes for the term.",
             [
                 ('print_instructions_B.png', None), ('approve_results_C.png', 'RESOLVE PENDING ISSUES'),
                 ('approve_results_D.png', 'TICK FOR APPROVED RESULTS'), ('approve_results_E.png', None)
             ]),
            ('View Results', 'Classes_Link', 'teacher_view_results',
             "You can view a class's results by going to class home page.  Once on the class home page to see a "
             "comparison graph of the class' results for a given test go to the "
             '"Tests Graphs" tab.  To see a graph of the results for one student go to the "Students Graphs" tab.  To '
             'see a graph of the results history of a student go to the "Previous Results" tab.  Note that results '
             'will only show for entries that have been approved.',
             [
                 ('print_instructions_B.png', None), ('view_results_C.png', 'VIEW RESULTS YOU WISH'),
                 ('approve_results_E.png', None), ('teacher_add_classes_D.png', None)
             ]),
            ('Completed', 'Classes_Link', None,
             "If you have finished all the steps you are done!  Use the program again when you are running tests for "
             "the term",
             None)
        ]
        step_divisions = [
            (1, 'Do this (unless already done by admin)'),
            (4, 'Running the tests'),
            (8, 'Do these steps after running tests'),
            (9, 'Completed')
        ]

        step_sets = []
        step_index = 0
        for step_index_to, steps_text in step_divisions:
            steps_formatted = []
            while step_index < step_index_to:
                (step_heading, tab_id_link, instructions_name, step_text, images) = steps[step_index]
                steps_formatted.append((step_index + 1, step_heading, tab_id_link, step_text,
                                        ('/instructions_page/' + instructions_name) if instructions_name else None,
                                        images))
                step_index += 1
            step_sets.append((steps_formatted, steps_text))

        context = {
            'logged_in_heading': heading,
            'user_name': request.session.get('username'),
            'user_tab_page_title': heading,
            'user_tabs': [
                ['Home', '/teacher_home/', 'user_home_page', 'Home_Link'],
                ['Classes', '/class/list/', 'item_list:1', 'Classes_Link']
            ],
            'step_sets': step_sets,
            'total_steps': len(steps)
        }

        return render(request, 'user_tab_page.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def teacher_home(request):
    if request.session.get('user_type', None) == 'Teacher':
        context = {
            'instructions_url': '/teacher_short_instructions/',
            'intro_text': [
                "This program provides resources for sessions in which you test your students' fitness, including "
                "instructions on how to run tests and lesson plans.",
                "It will also give you feedback on the students' nation wide percentile rankings and help you write "
                'reports.',
                'To use all these facilities you will need to follow the steps to the bottom left.  Click on each step '
                'to bring up instructions.'
            ]
        }
        return render(request, 'user_home_page.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def administrator_view(request):
    if request.session.get('user_type', None) == 'Administrator':

        administrator = Administrator.objects.get(user=User.objects.get(username=request.session.get('username')))

        steps = [
            ('Add Teachers', 'Teachers_Link', 'administrator_add_teacher',
             "Follow the diagrams to add all the PE teachers to the system.  When you're done click the "
             "<div class='arrow-right' style='display: inline-block'></div> above to see the next step.",
             [
                 ('add_teachers_B.png', None), ('add_teachers_D.png', None)
             ]),
            ('Add Classes For Term', 'Classes_Link', 'administrator_add_classes',
             "Follow the diagrams to add all teacher's classes for the term. "
             " **This step is optional and can be left to the teachers to do themselves**",
             [
                 ('administrator_add_class_B.png', None), ('administrator_add_class_D.png', None)
             ]),
            ('Completed', 'Classes_Link', None,
             "Once you have added all the PE teachers (and optionally the classes for the term) you are done!  "
             "The teachers will have received emails with their login details and can now login to the site.  You will "
             "need to come back to the site when/if you wish to add classes for next term or if more teachers need to "
             "be added to the system.  You can now logout.",
             None)
        ]
        step_divisions = [
            (1, 'Follow this step to add teachers for year'),
            (2, 'Optional Step (Can Leave For Teachers)'),
            (3, 'Completed')
        ]

        step_sets = []
        step_index = 0
        for step_index_to, steps_text in step_divisions:
            steps_formatted = []
            while step_index < step_index_to:
                (step_heading, tab_id_link, instructions_name, step_text, images) = steps[step_index]
                steps_formatted.append((step_index + 1, step_heading, tab_id_link, step_text,
                                        ('/instructions_page/' + instructions_name) if instructions_name else None,
                                        images))
                step_index += 1
            step_sets.append((steps_formatted, steps_text))

        context = {
            'logged_in_heading': 'Administrator (' + administrator.school_id.name + ')',
            'user_name': request.session.get('username'),
            'user_tab_page_title': 'Administrator: ' + administrator.school_id.name,
            'user_tabs': [
                ['Home', '/administrator_home/', 'user_home_page', 'Home_Link'],
                ['Teachers', '/teacher/list/', 'item_list:1', 'Teachers_Link'],
                ['Classes', '/class/list/', 'item_list:1', 'Classes_Link']
            ],
            'step_sets': step_sets,
            'total_steps': len(steps)
        }

        return render(request, 'user_tab_page.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def administrator_home(request):
    if request.session.get('user_type', None) == 'Administrator':
        context = {
            'instructions_url': '/administrator_short_instructions/',
            'intro_text': [
                'As an administrator you will need to:',
                '&nbsp&nbsp&nbsp&nbsp&nbsp 1. &nbsp&nbsp Add teachers to the teacher list',
                '&nbsp&nbsp&nbsp&nbsp&nbsp 2. &nbsp&nbsp Add classes for the teachers for the term (this step is '
                'optional and can be left to the teachers to do themselves)',
                '<br>',
                'To display instructions for step 1 click "Step 1: Add Teachers" to the bottom left of screen'
            ]
        }
        return render(request, 'user_home_page.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def superuser_view(request):
    if request.session.get('user_type', None) == 'SuperUser':

        context = {
            'logged_in_heading': 'Super User Page',
            'user_name': request.session.get('username'),
            'user_tab_page_title': 'Super User',
            'user_tabs': [
                ['Home', '/superuser_home/', 'user_home_page', 'Home_Link'],
                ['Schools', '/school/list/', 'item_list:1', 'Schools_Link'],
                ['Tests', '/test/list/', 'item_list:1', 'Tests_Link'],
                ['Test Categories', '/test_category/list/', 'item_list:1', 'Test_Categories_Link'],
                ['Major Test Categories', '/major_test_category/list/', 'item_list:1', 'Major_Test_Categories_Link']
            ]
        }

        return render(request, 'user_tab_page.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def superuser_home(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {'instructions_url': '/superuser_short_instructions/', 'intro_text': ['Super User']}
        return render(request, 'user_home_page.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def instructions_page(request, instructions_name):
    user_type = request.session.get('user_type', None)
    if (instructions_name == 'change_password') and (user_type in ('Administrator', 'Teacher')):
        context = {'heading': 'Change Password',
                   'reason': 'The first time you log in it is a good idea to '
                             'change your password to one that you want.',
                   'instructions': [
                       [('Click "Change Password" in the top right hand corner of the screen',
                         'change_password_A.png')],
                       [
                           ('Enter the details for your new password into the form that pops up',
                            'change_password_B.png'),
                           ('Then click the button at the bottom of the form and you are done!', None)
                       ]
                   ]}
    elif (instructions_name == 'administrator_add_teacher') and user_type == 'Administrator':
        context = {'heading': 'Add Teacher',
                   'reason': 'You need to add the PE teachers that will be using this program',
                   'instructions': [
                       [('Click the "Teachers" tab at the left of the screen (it may already be selected)',
                         'add_teachers_A.png')],
                       [('Click the "+" button at the top of the teachers table.', 'add_teachers_B.png')],
                       [
                           ('Enter the details for the teacher', 'add_teachers_C.png'),
                           ("Then click the button at the bottom of the form.  The teacher will be added and an email "
                            "with the teacher's login details will be sent to the email address you entered.", None)
                       ],
                       [('After you have added the teacher you will see them in teacher table.  If you have made a '
                         'mistake and you wish to edit the teacher then click the pencil to the right of the teacher.  '
                         'If you wish to delete the teacher then click the cross.', 'add_teachers_D.png')],
                       [("Repeat from point 2. for all the remaining PE teachers you wish to add and you are done! "
                         "(don't forget to add yourself if you are a PE teacher).", None)]
                   ]}
    elif instructions_name == 'administrator_add_classes' and user_type == 'Administrator':
        context = {'heading': 'Add Classes',
                   'reason': 'After the teachers have been added you may wish to assign some or all of the classes for '
                             'the term.  Alternatively the teachers may add their own classes themselves when they '
                             'login.  This decision is up to you (it is fairly simple for either of you to do it).',
                   'instructions': [
                       [('Click the "Classes" tab at the left of the screen (it may already be selected)',
                         'administrator_add_class_A.png')],
                       [('Click the "+" button at the top of the classes table.', 'administrator_add_class_B.png')],
                       [
                           ('Enter the details for the class.  When entering the class name you should give the term '
                            'as well e.g. "Class 9C Term 1".  The drop down has a list of the teachers that you have '
                            'already added.  If the teacher for this class is not available then you must add them '
                            "<div class='link_open_tab' style='display: inline'><a href='administrator_add_teacher'>"
                            "(see instructions)</a></div>.", 'administrator_add_class_C.png'),
                           ('Then click the button at the bottom of the form', None)
                       ],
                       [
                           ('The next step is to select the tests that you want the class to perform over the term.  '
                            'A default set of tests is originally selected.', None),
                           ("Click the check boxes of tests you wish to change. (see the 'A' in the diagram below)",
                            None),
                           ("You can see instructions for the tests by clicking on the green icons. (see the 'B')",
                            None),
                           ("You can reselect the default set of tests or select the tests someone has previously "
                            "used in another class.  Note that not all of the previous classes will be displayed.  If "
                            "more than one class has used the same set of tests then only one of these classes will be "
                            "listed. (see the 'C')", None),
                           ("Once you are finished selecting the classes click the button at the bottom of the form "
                            "and the class will be added.  Note that you can change these selected tests later. "
                            "(see the 'D')", 'administrator_add_class_D.png')
                       ],
                       [('After you have added the class you will see it in class table.  If you have made a '
                         'mistake and you wish to edit the class then click the pencil to the right of the class.  '
                         'If you wish to delete the class then click the cross.', 'administrator_add_class_E.png')],
                       [('Repeat from point 2. for all the remaining classes for the term and you are done!', None)],
                       [("It is recommended that you add all classes this way the first time you do this, in future "
                         "you could try to add classes from a file which may be quicker "
                         "<div class='link_open_tab' style='display: inline'>"
                         "<a href='administrator_add_classes_from_file'>(see instructions)</a></div>.", None)]
                   ]}
    elif instructions_name == 'administrator_add_classes_from_file' and user_type == 'Administrator':
        context = {'heading': 'Add Classes From File',
                   'reason': 'It can be quicker to add all classes for the term from a file.  However you should not '
                             'do this the first time you add classes.',
                   'instructions': [
                       [
                           ('To make a classes CSV file first you must open up a new excel document.', None),
                           ('Next put the following into the first cells of the excel sheet.',
                            'administrator_add_classes_A.png'),
                           ("Then put the details for the classes you are adding under the headings  (an example is "
                            " below).  If you leave the last cell blank for any classes than the default set of "
                            "tests will be allocated instead of a previous class' tests.  Note though you must still "
                            "include the heading even if you leave the cells blank for all classes).",
                            'administrator_add_classes_B.png'),
                           ('Next you will need to save or export the excel document as a .CSV file.  If you do not '
                            'know how to do this then you will need to look up how on line.  Be sure to make the '
                            '"field delimiter" a comma (,) and the "text delimiter" a double quote (").  Also be sure '
                            'choose the "quote all text cells option".  The options window may look something like '
                            'this', 'administrator_add_classes_C.png'),
                           ('After you have saved the file you can open it in Notepad or WordPad to check it.  It '
                            'should look something like the example below.', 'administrator_add_classes_D.png'),
                           ('Check that there are double quotes around all of the text (everything except for the '
                            'year)', None),
                           ('If everything looks good you are now ready to upload the file', None)
                       ],
                       [
                           ('Now that the file is ready you can go back to the program to upload it.', None),
                           ('Click the "Classes" tab at the left of the screen (it may already be selected)',
                            'administrator_add_class_A.png')
                       ],
                       [
                           ('Go to the "Add Class(es)" menu at the top of the Class table and select the "Add Classes" '
                            'option', 'administrator_add_classes_E.png')
                       ],
                       [
                           ('Browse and select the .CSV file you just created.', 'administrator_add_classes_F.png'),
                           ('Then click the button at the bottom of the form (it may take a little time to add the '
                            'classes so be patient)', None)
                       ]
                   ]}
    elif instructions_name == 'teacher_add_classes' and user_type == 'Teacher':
        context = {'heading': 'Add Classes',
                   'reason': 'If the administrator has not already assigned your classes for the term than you will '
                             'need to do so yourself',
                   'instructions': [
                       [('Click the "Classes" tab at the left of the screen (it may already be selected)',
                         'teacher_add_class_A.png')],
                       [('Click the "+" button at the top of the classes table.', 'teacher_add_class_B.png')],
                       [
                           ('Enter the details for the class.  When entering the class name you should give the term '
                            'as well e.g. "Class 9C Term 1".', 'teacher_add_class_C.png'),
                           ('Then click the button at the bottom of the form', None)
                       ],
                       [('After you have added the class you will see it in class table.  If you have made a '
                         'mistake and you wish to edit the class then click the pencil to the right of the class.  '
                         'If you wish to delete the class then click the cross.', 'teacher_add_class_D.png')],
                       [('Repeat from point 2. for all your remaining classes and you are done!.  Note that you will '
                         'need to add a new set of classes for every term you intend to run the tests in.', None)]
                   ]}
    elif instructions_name == 'teacher_print_instructions' and user_type == 'Teacher':
        context = {'heading': 'Print Instructions',
                   'reason': 'Once you have classes assigned this program will provide aides for running the tests',
                   'instructions': [
                       [
                           ('Click the "Classes" tab at the left of the screen (it may already be selected)',
                            'teacher_add_class_A.png'),
                           ('Then in the classes table click on the home page symbol for the class that you want to '
                            'run tests for', 'print_instructions_B.png')
                       ],
                       [
                           ('Check that the set of tests you want to run are allocated to the class.  You may need to '
                            'scroll to the right to see all of them', 'print_instructions_C.png'),
                           ("If there are any tests that you wish to add or remove click the 'T' symbol and then make "
                            "the changes", 'print_instructions_D.png')
                       ],
                       [
                           ('Once all the tests are correct you can print them off.  Click the printer symbol.',
                            'print_instructions_E.png'),
                           ('In the tab that opens click the print instructions button', 'print_instructions_F.png'),
                           ('After you have printed the tab that opened will close automatically', None)
                       ],
                       [
                           ('You should print off the instructions for every class you are teaching (unless one class '
                            'has the same set of tests as another then you only need to print once)', None),
                           ('To print for other classes repeat from point 1 (be sure to click the "Classes" tab).',
                            None)
                       ]
                   ]}
    elif instructions_name == 'teacher_print_results_entry' and user_type == 'Teacher':
        context = {'heading': 'Print Student Entry Results Sheet',
                   'reason': 'This step will give you a print out that the students can write their results in when '
                             'they are performing the tests.  Later they will enter these results into the system.',
                   'instructions': [
                       [
                           ('Click the "Classes" tab at the left of the screen (it may already be selected)',
                            'teacher_add_class_A.png')
                       ],
                       [
                           ('Next in the classes table click on the "print entry sheet" symbol for the class that '
                            'you want to run tests for', 'print_results_entry_C.png'),
                           ('In the tab that opens click the print student results entry sheet button',
                            'print_results_entry_D.png'),
                           ('Make sure to make enough copies for all the students in the class.', None),
                           ('After you have printed the tab that opened will close automatically', None)
                       ],
                       [
                           ('Now you will need to get the result entry sheets for your other classes.  '
                            'To do this repeat from point 2.', None)
                       ]
                   ]}
    elif instructions_name == 'teacher_get_login_details' and user_type == 'Teacher':
        context = {'heading': 'Get Class Login Details',
                   'reason': 'Once the students have completed the tests and noted their results they will need to '
                             'enter them into the system.  For each class you will need to get a username and password '
                             'for the students to login with.',
                   'instructions': [
                       [
                           ('Click the "Classes" tab at the left of the screen (it may already be selected)',
                            'teacher_add_class_A.png')
                       ],
                       [
                           ('Next in the classes table click on the "reset/get new login" symbol for the class that '
                            'you want to run tests for', 'get_login_C.png'),
                           ('Then note down the login and password that is displayed and then click done',
                            'get_login_D.png'),
                           ('If at a later time you forget the login/password or you want to reset the password then '
                            'you can click this link again.  Each time you click it you will reset the password to a '
                            'new one.', None)
                       ],
                       [
                           ('Now you will need to get login details for your other classes.  To do this repeat from '
                            'point 2.', None)
                       ]
                   ]}
    elif instructions_name == 'student_enter_results' and user_type == 'Teacher':
        context = {'heading': 'Get Students To Enter Results',
                   'reason': 'Once each class has a login the student can enter their results.  Each of the students '
                             'will need access to a computer for doing this.',
                   'instructions': [
                       [
                           ('Now the students can login.  To do this get each of the students to go to the site home '
                            'page and enter the login and password obtained in the previous step',
                            'enter_results_A.png'),
                           ('The site address is ' + web_address, None),
                           ('If you are using the one computer than you will first need to logout', None)
                       ],
                       [
                           ('Now each student can enter their results.  First they should fill in the student '
                            'details.', 'enter_results_B.png'),
                           ('Then the results', 'enter_results_C.png'),
                           ('Make sure the results are entered with the units given next to each result entry box',
                            'enter_results_D.png')
                       ],
                       [
                           ('After the results have been entered click the "Save Results" button at the bottom of the '
                            'screen', 'enter_results_E.png'),
                           ('If all the results have been entered correctly than the student should now see graphs of '
                            'their results.  If they wish they can take a screen shot of the results.  Once they '
                            'click "Done" at the bottom of the screen they will be logged out.', 'enter_results_F.png'),
                           ('If the results were not all entered correctly than there will be some red text next to '
                            'the boxes that need to be amended', 'enter_results_G.png'),
                           ('If the graphs show up as all 0 than it may be that the student has entered in the '
                            'wrong age (and so there is no percentile information for that age)', None)
                       ]
                   ]}
    elif instructions_name == 'teacher_approve_entries' and user_type == 'Teacher':
        context = {'heading': 'Approve Entries',
                   'reason': 'After the students have entered their results you must check that they have entered '
                             'them correctly.  This can also be done while the students are entering there results if '
                             'you have a separate computer.',
                   'instructions': [
                       [
                           ('Click the "Classes" tab at the left of the screen (it may already be selected)',
                            'teacher_add_class_A.png'),
                           ('Then in the classes table click on the home page symbol for the class that you wish to '
                            'approve results for', 'print_instructions_B.png')
                       ],
                       [
                           ('You should see a table with some results in it.  If you notice an "!" next to any of the '
                            'names then there are some pending issues to resolve.  Pending issues can arise from '
                            'different causes (mainly due to a student entering in the wrong details).  '
                            'The system will detect for instance if the same student has entered results twice, if two '
                            'students enter the same student number, if a student already in the database has very '
                            'similar details but one is different or if the student age is outside the normal age for '
                            'a high school student.  If there are any issues showing click on the "!" symbol next '
                            'to the student to resolve it.', 'approve_results_C.png'),
                           ('You will then see a pop up dialog.  Make sure to read it carefully before going onto the '
                            'next step', 'approve_results_D.png'),
                           ("Hopefully the dialog can help you to resolve the issue but if not you can edit the "
                            "results directly by clicking the pencil symbol to the right of the student's results.  "
                            "If there are a lot of tests you may need to scroll the table to the right to see the "
                            "pencil symbol.  You can also delete a student entry (and perhaps get them to re-enter it) "
                            "by clicking the cross symbol next to the pencil", 'approve_results_E.png')
                       ],
                       [
                           ('Once the pending issues for a student have been resolved (or there were none to start '
                            'with) you should check their results to make sure they were entered correctly (the '
                            'student may have made a mistake or tried to make their results look more flattering).  '
                            'If there are a lot of tests you may need to scroll the table to the right to see them '
                            'all.  If you need to amend anything you can do so by clicking the pencil symbol to the '
                            'right of the results (again you may need to scroll).  You can also delete the whole '
                            'entry (and perhaps get the student to re-enter the results) by clicking the cross symbol '
                            'next to the pencil.', 'approve_results_E.png'),
                           ('If you do edit the results than make sure to save the results at the end by clicking the '
                            '"Save Results" button at the bottom of the form.', None)
                       ],
                       [
                           ("Once you are satisfied that a student's results are entered correctly you can approve the "
                            "student.  To do this click the empty check box next to the student's name",
                            'approve_results_G.png'),
                           ('Then click the "Approve Student Result Entry" button of the form that pops up',
                            'approve_results_H.png'),
                           ('You should now see a tick in the check box.  If you have made a mistake and you want to '
                            'un-approve the student you can click on this symbol.', 'approve_results_I.png')
                       ],
                       [
                           ('You can also approve all the students at once instead of clicking on each of the check '
                            'boxes individually.  However before you do this make sure that you are satisfied that all '
                            'the results are correct.  To approve all click the tick in the menus',
                            'approve_results_J.png'),
                           ('Then click the "Approve All Student Entry Results" in the dialog that pops up',
                            'approve_results_K.png')
                       ],
                       [
                           ('To approve results for other classes repeat from point 1  (be sure to click the "Classes" '
                            'tab)', None)
                       ]
                   ]}
    elif instructions_name == 'teacher_view_results' and user_type == 'Teacher':
        context = {'heading': 'View Results',
                   'reason': 'After the student results have been entered and approved you can view these results '
                             'in different forms',
                   'instructions': [
                       [
                           ('Click the "Classes" tab at the left of the screen (it may already be selected)',
                            'teacher_add_class_A.png'),
                           ('Then in the classes table click on the home page symbol for the class that you wish to '
                            'view results for', 'print_instructions_B.png'),
                           ('There are 4 different formats that you can view the data listed in the following 4 '
                            'points', None)
                       ],
                       [
                           ('Initially you will see the class results table', 'view_results_C.png'),
                           ('This can also be accessed by clicking the "Results Table" class panel option',
                            'view_results_D.png'),
                           ('If there are a lot of tests in the table you may need to scroll right on the table to see '
                            'all of the results', 'view_results_E.png')
                       ],
                       [
                           ('A graph of the results of the class for a given test can be viewed by first clicking the '
                            '"Tests Graphs" class panel option', 'view_results_F.png'),
                           ('Next select the test you want to view results for', 'view_results_G.png'),
                           ('The resulting graph will show percentiles rankings for each of the students for that '
                            'test.  Note that 2 students with the same result on a test may have a different '
                            'percentile ranking if they are different ages', 'view_results_H.png')
                       ],
                       [
                           ('A graph of the results for a student can be viewed by first clicking the "Students '
                            'Graphs" class panel option', 'view_results_I.png'),
                           ('Next select the student you want to view results for', 'view_results_J.png'),
                           ('The resulting graph(s) will show percentiles rankings for the student for the different '
                            'tests.  There will be one graph per major test category.  The color of the bars in each '
                            'graph represents a minor test category', 'view_results_K.png')
                       ],
                       [
                           ('Previous results for a student can be viewed by clicking the "Previous Graphs" class '
                            'panel option.  This is only useful if a student has results entered into the system from '
                            'previous classes', 'view_results_L.png'),
                           ('Next select the student you want to view results for', 'view_results_M.png'),
                           ('The resulting graphs will show the percentiles rankings for tests from previous classes '
                            'for the chosen student', 'view_results_N.png')
                       ],
                       [
                           ('Repeat from point 1 to view results for other classes  (be sure to click the "Classes" '
                            'tab)', None)
                       ]
                   ]}
    else:
        context = {'heading': 'No Heading Given'}

    return render(request, 'user_instructions.html', RequestContext(request, context))


def school_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(school, school.get_display_items()) for school in School.objects.all()],
            'menu_label': 'Add School',
            'item_list_table_headings': School.get_display_list_headings(),
            'item_list_buttons': [
                ('+', 'item_list_modal_load_link', '/school/add/', 'Add School'),
                ('++', 'item_list_modal_load_link', '/school/adds/', 'Add/Edit Schools From .CSV')
            ],
            'item_list_options': [
                ['item_list_modal_load_link', '/school/edit/', 'pencil', 'edit school'],
                ['item_list_modal_load_link', '/school/reset_password/', 'repeat', 'reset administrator password'],
                ['item_list_modal_load_link', '/school/delete/', 'remove', 'delete school']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


def test_category_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(test_category, test_category.get_display_items())
                          for test_category in TestCategory.objects.all()],
            'menu_label': 'Add Test Category',
            'item_list_table_headings': TestCategory.get_display_list_headings(),
            'item_list_buttons': [
                ('+', 'item_list_modal_load_link', '/test_category/add/', 'Add Test Category'),
                ('++', 'item_list_modal_load_link', '/test_category/adds/', 'Add/Edit Test Categories From .CSV')
            ],
            'item_list_options': [
                ['item_list_modal_load_link', '/test_category/edit/', 'pencil', 'edit test category'],
                ['item_list_modal_load_link', '/test_category/delete/', 'remove', 'delete test category']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


def major_test_category_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(major_test_category, major_test_category.get_display_items())
                          for major_test_category in MajorTestCategory.objects.all()],
            'menu_label': 'Add Major Test Category',
            'item_list_table_headings': MajorTestCategory.get_display_list_headings(),
            'item_list_buttons': [
                ('+', 'item_list_modal_load_link', '/major_test_category/add/', 'Add Major Test Category'),
                ('++', 'item_list_modal_load_link', '/major_test_category/adds/', 'Add/Edit Major Test Categories From '
                                                                                  '.CSV')
            ],
            'item_list_options': [
                ['item_list_modal_load_link', '/major_test_category/edit/', 'pencil', 'edit major test category'],
                ['item_list_modal_load_link', '/major_test_category/delete/', 'remove', 'delete major test category']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


def test_list(request):
    if request.session.get('user_type', None) == 'SuperUser':
        context = {
            'item_list': [(test, test.get_display_items())
                          for test in Test.objects.all()],
            'menu_label': 'Add Test',
            'item_list_table_headings': Test.get_display_list_headings(),
            'item_list_buttons': [
                ('+', 'item_list_modal_load_link', '/test/adds/', 'Add Tests From .CSVs'),
                ('T', 'item_list_modal_load_link', '/allocate_default_tests/', 'Allocate Default Tests')
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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


def test_instructions(request, test_pk):
    user_type = request.session.get('user_type', None)
    if (user_type == 'Administrator') or (user_type == 'Teacher'):
        context = get_test_instructions_context(test_pk)
        context['showing_individual_test'] = True
        return render(request, 'test_instructions.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def get_test_instructions_context(test_pk):
    test = Test.objects.get(pk=test_pk)
    test_name = test.test_name
    if test_name == 'Sit and Reach':
        context = {'heading': 'Sit and Reach Test',
                   'objective': "The objective of this test is to monitor the development of the athlete's hip and"
                                " trunk flexibility.",
                   'resources': ['Wall', 'Box', 'Tape', 'Metre Ruler', 'Assistant'],
                   'instructions': [[
                       'The athlete warms up for 10 minutes and then removes their shoes',
                       'The assistant secures the ruler to the box top with the tape so that the front edge of '
                       'the box lines up with the zero mark on the ruler and the zero end of the ruler points '
                       'towards the athlete',
                       'The athlete sits on the floor with their legs fully extended with the bottom of their bare '
                       'feet against the box',
                       'The athlete places one hand on top of the other, slowly bends forward and reaches along '
                       'the top of the ruler as far as possible holding the stretch for two seconds',
                       "The assistant records the distance reached by the athlete's finger tips",
                       'The athlete performs the test three times',
                       'The assistant calculates and records the average of the three distances'
                   ]],
                   'diagram': 'sit_and_reach.png'}
    elif test_name == 'Abdominal Test':
        context = {'heading': '8 Stage Abdominal Test',
                   'objective': 'The 8-level sit up test measures abdominal strength, which is important in back '
                                'support and core stability.',
                   'resources': ['Flat surface', '5 lb (2.5 kg)', '10 lb (5 kg) weight',
                                 'recording sheet and pen.'],
                   'instructions': [[
                       'The subject lies on their back, with their knees at right angles and feet flat on the '
                       'floor.',
                       'The subject then attempts to perform one complete sit-up for each level in the '
                       'prescribed manner (see diagram below), starting with level 1. Each level is achieved if '
                       'a single sit up is performed in the prescribed manner, without the feet coming off the '
                       'floor. Three attempts can be made at each level. Failure on the fourth attempt, results '
                       'in the previous level being recorded as the result.'
                   ]],
                   'diagram': 'abdominal_test.png'}
    elif test_name == 'Sit Ups 60sec':
        context = {'heading': '60sec Sit Up Test',
                   'objective': "The objective of this test is to monitor the muscular endurance of the athlete's "
                                "abdominals.",
                   'resources': ['Non-slip surface', 'Exercise mat', 'Stopwatch', 'Assistant'],
                   'instructions': [
                       ['This test requires the athlete to perform as many sit-ups as possible in 60 seconds.'],
                       [
                           'The athlete warms up for 10 minutes',
                           'The athlete lies on the mat with the knees bent, feet flat on the floor and their '
                           'hands on their ears where they must stay throughout the test',
                           "The assistant holds the athlete's feet on the ground",
                           'The assistant gives the command "GO" and starts the stopwatch',
                           'he athlete sits up touching the knees with their elbows, then returns back to the '
                           'floor and continues to perform as many sit-ups as possible in 60 seconds',
                           'The assistant keeps the athlete informed of the time remaining',
                           "The assistant counts and records the number of correct sit-ups completed in the 60 "
                           "seconds and uses this recorded value to assess the athlete's performance"
                       ]
                   ]}
    elif test_name == 'Push Ups':
        context = {'heading': '30sec Push Up Test',
                   'objective': "The objective of the 30sec Press Up test is to assess the muscular endurance of "
                                "the athlete's upper body muscles.",
                   'resources': ['Non-slip surface', 'Assistant'],
                   'instructions': [[
                       'The athlete warms up for 10 minutes',
                       'The athlete lies on the ground, places their hands by the shoulders and straightens their '
                       'arms (see Figure 1 below)',
                       'The athlete lowers the body until the elbows reach 90 degrees (see Figure 2 below) and '
                       'then extends the arms to return to the start position',
                       'The athlete continuous this press-up action, with no rest for 30 seconds',
                       'The assistant counts and records the number of correctly completed press-ups'
                   ]],
                   'diagram': ['push_ups1.png', 'push_ups2.png'],
                   'multiple_diagrams': True}
    elif test_name == 'Beep Test':
        context = {'heading': 'Beep Test',
                   'objective': "The objective of the Multi-Stage Fitness Test (MSFT) (as described in a paper by "
                                "Leger & Lambert in 1982), is to monitor the development of the athlete's "
                                "cardiovascular endurance and their maximum oxygen uptake (VO2max).",
                   'resources': ['Flat non-slip surface', '30 metre tape measure', 'Marking cones',
                                 'The Multi-Stage Fitness Test CD', 'CD Player', 'Recording sheets', 'Assistant'],
                   'instructions': [
                       ['This test requires the athlete to run 20m in time with a beep from a CD recording. The '
                        'athlete must place one foot on or beyond the 20m marker at the end of each shuttle.'],
                       ['The athlete warms up for 10 minutes',
                        'The assistant measures out a 20 metre section and marks each end with marker cones',
                        'If the athlete arrives at the end of a shuttle before the beep, the athlete must wait for '
                        'the beep and then resume running',
                        'If the athlete fails to reach the end of the shuttle before the beep they should be '
                        'allowed 2 further shuttles to attempt to regain the required pace before being withdrawn',
                        'The assistant records the level and number of shuttles completed at that level by the '
                        'athlete when they are withdrawn']
                   ]}
    elif test_name == 'Flexed Arm Hang':
        context = {'heading': 'Flexed Arm Hang',
                   'objective': "The objective of this test is to monitor the muscular endurance of the athlete's "
                                "arms and back.",
                   'resources': ['Bar above head height', 'Stopwatch', 'Assistant'],
                   'instructions': [
                       ['This test requires the athlete to perform and hold a chin up position, using a bar above '
                        'head height, for as long as possible.'],
                       ['The athlete warms up for 10 minutes',
                        'The athlete uses a flexed arm hang position with the palms of the hand facing them',
                        'Using their arms the athlete raises their chin above the bar to the "start position"',
                        'Once the athlete is in the "start position" the assistant starts the stopwatch',
                        'The athlete is to maintain the "start position" for as long as possible',
                        "The assistant stops the stopwatch when the athlete's chin drops below the top of the bar",
                        'The assistant records the time the "start position" was held for']
                   ],
                   'diagram': 'flexed_arm_hang.png'}
    elif test_name == 'Agility Run':
        context = {'heading': 'Illinois Agility Test',
                   'objective': "The objective of the Illinois Agility Run Test (as described in a paper by "
                                "Getchell in 1979) is to monitor the development of the athlete's agility.",
                   'resources': ['Flat non-slip surface', '8 cones', 'Stopwatch', 'Assistant'],
                   'instructions': [
                       ['This test requires the athlete to run the red line route (see diagram below) as fast as '
                        'possible.'],
                       ['The athlete warms up for 10 minutes',
                        'The assistant sets up the course as detailed in the diagram',
                        'The athlete lies face down on the floor at the "Start" cone',
                        'The assistant gives the command "GO" and starts the stopwatch',
                        'The athlete jumps to his/her feet and negotiates the course around the cones following '
                        'the red line route shown in the diagram to the finish',
                        'The assistant stops the stopwatch and records the time when the athlete passes the '
                        '"Finish" cone']
                   ],
                   'diagram': 'agility_run.png'}
    elif test_name == 'Standing Stork':
        context = {'heading': 'Standing Stork Test',
                   'objective': "To monitor the development of the athlete's ability to maintain a state of "
                                "equilibrium (balance).",
                   'resources': ['Warm dry location - gym', 'Stopwatch', 'Assistant'],
                   'instructions': [[
                       'The athlete stands comfortably on both feet with their hands on their hips',
                       'The athlete lifts the right leg and places the sole of the right foot against the side of '
                       'the left kneecap',
                       'The assistant gives the command "GO", starts the stopwatch and the athlete raises the heel '
                       'of the left foot to stand on their toes',
                       'The athlete is to hold this position for as long as possible',
                       "The assistant stops the stopwatch when the athlete's left heel touches the ground or the "
                       "right foot moves away from the left knee",
                       'The assistance records the time',
                       'The athlete rests for 1 minute',
                       'The athlete stands comfortably on both feet with their hands on their hips',
                       'The athlete lifts the left leg and places the sole of the left foot against the side of '
                       'the right kneecap',
                       'The assistant gives the command "GO", starts the stopwatch and the athlete raises the heel '
                       'of the right foot to stand on their toes',
                       'The athlete is to hold this position for as long as possible',
                       "The assistant stops the stopwatch when the athlete's right heel touches the ground or the "
                       "left foot moves away from the right kneecap",
                       'The assistant records the time',
                       'Left and right standing position times are then averaged out with average time recorded on '
                       'the results sheet'
                   ]],
                   'diagram': 'standing_stork.png'}
    elif test_name == 'Ruler Drop':
        context = {'heading': 'Ruler Drop Test',
                   'objective': "The objective of this test is to monitor the athlete's reaction time",
                   'resources': ['Metre ruler', 'Assistant', 'A bench or platform'],
                   'instructions': [[
                       "The ruler is held by the assistant between the outstretched index finger and thumb of the "
                       "athlete's dominant hand, so that the top of the athlete's thumb and index finger is level "
                       "with the 50 centimetre line on the ruler.",
                       'The assistant instructs the athlete to press their fingers together as soon as possible '
                       'after the ruler has been released',
                       'The assistant releases the ruler and the athlete clamps down on the ruler between their '
                       'index finger and thumb as quick as possible',
                       "The assistant is to record the distance between the 50cm mark on the ruler and the top of "
                       "the athlete's thumb where the ruler has been caught",
                       'The test is repeated 2 more times and the average value is recorded'
                   ]]}
    elif test_name == 'Catch':
        context = {'heading': 'Tennis Ball Test',
                   'objective': "The objective of the test is to monitor the athlete's Hand Eye coordination.",
                   'resources': ['Tennis Ball', 'Stopwatch', 'Smooth Wall', 'Assistant'],
                   'instructions': [
                       ['This test requires the athlete to throw and catch a tennis ball off a wall.'],
                       ['The athlete stands two metres away from a smooth wall',
                        'The assistant gives the command "GO" and starts the stopwatch',
                        'The athlete throws a tennis ball with their right hand against the wall and catches it '
                        'with the left hand, throws the ball with the left hand and catches it with the right '
                        'hand. This cycle of throwing and catching is repeated for 30 seconds',
                        'The assistant counts the number of catches and stops the test after 30 seconds',
                        'The assistant records the number of catches',
                        'Once instructions are given, allow the athlete to practice for 2minutes prior to the test']
                   ]}
    elif test_name == 'Sprint 20m':
        context = {'heading': '20 metre Sprint Test',
                   'objective': "The objective of this test is to monitor the development of the athlete's ability "
                                "to effectively and efficiently build up acceleration, from a standing start to "
                                "maximum speed.",
                   'resources': ['Measuring Tape', 'Cones', 'Flat non-slip surface', 'Stopwatch', 'Assistant'],
                   'instructions': [
                       ['This test requires the athlete to sprint as fast as possible over 20 metres'],
                       ['The athlete warms up for 5 minutes',
                        'The assistant marks out a 20 metre straight section with cones from a wall or tag line',
                        "The athlete starts running slowly towards wall/ tag line, the stopwatch is started when "
                        "the athlete turns and their hand comes off the wall or the tag is taken. The stopwatch "
                        "stops when the athlete's torso crosses the finish line.",
                        'The test is conducted 3 times',
                        "The assistant uses the fastest recorded time to assess the athlete's performance"]
                   ]}
    elif test_name == 'Vertical Jump':
        context = {'heading': 'Vertical Jump Test',
                   'objective': "To monitor the development of the athlete's power, through the legs.",
                   'resources': ['Wall', 'Tape measure', 'Step Ladder', 'Chalk', 'Assistant'],
                   'instructions': [
                       ['The athlete warms up for 10 minutes',
                        'The athlete chalks the end of his/her finger tips',
                        "The athlete stands side onto the wall, keeping both feet remaining on the ground, reaches "
                        "up as high as possible with one hand and marks the wall with the tips of the fingers "
                        "(M1 - See diagram below)",
                        'The athlete from a static position jumps as high as possible and marks the wall with the '
                        'chalk on his/ her fingers (M2 - See diagram below)',
                        "The assistant measures and records the distance between M1 and M2",
                        'The athlete repeats the test 3 times',
                        "The assistant calculates the average of the recorded distances and uses this value to "
                        "assess the athlete's performance"]
                   ],
                   'diagram': 'vertical_jump.png'}
    elif test_name == 'Basketball Throw':
        context = {'heading': 'Basketball Wall Throw Test',
                   'objective': "This test measures upper body (arm) power. By keeping the back in contact with "
                                "the wall the strength of the arms are tested.",
                   'resources': ['Wall', 'Tape measure', 'Basketball (size 7 boys) (size 6 Girls)', 'Assistant'],
                   'instructions': [
                       ['The athlete sits on the floor with his/ her legs fully extended and their back against a '
                        'wall',
                        'The ball is held with the hands on the side and slightly behind the centre of the ball',
                        "The athlete then presses their hands up against their chest",
                        'With the forearms positioned parallel to the ground',
                        "The athlete then throws the basketball as firmly as they can, as far as they can straight "
                        "forward, while maintaining their back against the wall",
                        'The distance thrown is then recorded by the assistant',
                        "The test is repeated 3 times, with the best result recorded"]
                   ]}
    else:
        context = {'heading': 'Test Instructions Not Found'}
    context['test'] = test
    return context


def allocate_default_tests(request):
    if request.session.get('user_type', None) == 'SuperUser':
        if request.POST:
            allocate_default_tests_form = AllocateEditDefaultTestsForm(data=request.POST)
            if allocate_default_tests_form.allocate_default_tests():
                context = {'finish_title': 'Default Tests Allocated',
                           'user_message': 'Default Tests Allocated Successfully'}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/allocate_default_tests/',
                           'functionality_name': 'Allocate Default Tests',
                           'allocate_tests_form': allocate_default_tests_form,
                           'info_load_class': 'test_instructions_load_link'}
                return render(request, 'modal_form_allocate_tests.html', RequestContext(request, context))
        else:
            context = {'post_to_url': '/allocate_default_tests/',
                       'functionality_name': 'Allocate Default Tests',
                       'allocate_tests_form': AllocateEditDefaultTestsForm(),
                       'info_load_class': 'test_instructions_load_link'}
            return render(request, 'modal_form_allocate_tests.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def teacher_list(request):
    if request.session.get('user_type', None) == 'Administrator':
        username = request.session.get('username', None)
        school = Administrator.objects.get(user=User.objects.get(username=username)).school_id
        context = {
            'item_list': [(teacher, teacher.get_display_items())
                          for teacher in Teacher.objects.filter(school_id=school)],
            'menu_label': 'Add Teacher',
            'item_list_table_headings': Teacher.get_display_list_headings(),
            'item_list_buttons': [
                ('+', 'item_list_modal_load_link', '/teacher/add/', 'Add Teacher')
            ],
            'item_list_options': [
                ['item_list_modal_load_link', '/teacher/edit/', 'pencil', 'edit teacher'],
                ['item_list_modal_load_link', '/teacher/reset_password/', 'repeat', 'reset teacher password'],
                ['item_list_modal_load_link', '/teacher/delete/', 'remove', 'delete teacher']
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


def class_list(request):
    user_type = request.session.get('user_type', None)
    if (user_type == 'Administrator') or (user_type == 'Teacher'):
        user = User.objects.get(username=request.session.get('username', None))
        item_list_add_buttons = [('+', 'item_list_modal_load_link', '/class/add/', 'Add Class')]
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
            item_list_add_buttons.append(('++', 'item_list_modal_load_link', '/class/adds/', 'Add Classes From File'
                                                                                             ' (Advanced)'))
        context = {
            'item_list': class_items,
            'menu_label': 'Add Class(es)',
            'item_list_table_headings': class_list_headings,
            'item_list_buttons': item_list_add_buttons,
            'item_list_options': [
                ('item_list_modal_load_link', '/class/edit/', 'pencil', 'edit class'),
                ('test_instructions_load_link', '/class/print_test_instructions/', 'print',
                 'print class test instructions'),
                ('test_instructions_load_link', '/class/print_student_results_sheet/', 'list-alt',
                 'print student results entry sheet'),
                ('modal_load_link', '/class/get_new_code/', 'repeat', 'reset/get new class login password'),
                ('class_load_link', '/class/class/', 'home', 'go to class page'),
                ('item_list_modal_load_link', '/class/delete/', 'remove', 'delete class')
            ]
        }
        return render(request, 'item_list.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def class_add(request, load_from_class_pk=None):
    user_type = request.session.get('user_type', None)
    if (user_type == 'Administrator') or (user_type == 'Teacher'):
        user = User.objects.get(username=request.session.get('username', None))
        teacher_or_administrator = (Teacher if user_type == 'Teacher' else Administrator).objects.get(user=user)
        school_pk = teacher_or_administrator.school_id.pk
        if request.POST:

            class_add_form = (AddClassTeacherForm(teacher_pk=teacher_or_administrator.pk, data=request.POST)
                              if user_type == 'Teacher' else AddClassForm(school_pk=school_pk, data=request.POST))
            if load_from_class_pk:
                allocate_tests_form = AllocateTestsToClassForm(load_from_class_pk=load_from_class_pk)
            else:
                allocate_tests_form = AllocateTestsToClassForm(data=request.POST)

            if request.POST['button_pressed'] == 'next':
                if class_add_form.is_valid():
                    context = {'post_to_url': '/class/add/',
                               'modal_title': 'Choose Tests For Class',
                               'first_page': False,
                               'class_add_form': class_add_form,
                               'other_classes': get_other_classes(url_prefix='/class/add/', school_pk=school_pk),
                               'allocate_tests_form': allocate_tests_form,
                               'info_load_class': 'test_instructions_load_link'}
                    return render(request, 'modal_form_add_class.html', RequestContext(request, context))
                else:
                    context = {'post_to_url': '/class/add/',
                               'modal_title': 'Enter Class Details',
                               'first_page': True,
                               'class_add_form': class_add_form,
                               'allocate_tests_form': allocate_tests_form,
                               'info_load_class': 'test_instructions_load_link'}
                    return render(request, 'modal_form_add_class.html', RequestContext(request, context))
            elif request.POST['button_pressed'] == 'back':
                context = {'post_to_url': '/class/add/',
                           'modal_title': 'Enter Class Details',
                           'first_page': True,
                           'class_add_form': class_add_form,
                           'allocate_tests_form': allocate_tests_form,
                           'info_load_class': 'test_instructions_load_link'}
                return render(request, 'modal_form_add_class.html', RequestContext(request, context))
            else:
                if allocate_tests_form.is_valid():
                    class_instance = class_add_form.add_class()
                    if class_instance:
                        allocate_tests_form.allocate_tests_to_class(class_instance.pk)
                        class_display_text = (class_instance.class_name + ' (' + str(class_instance.year) + ')')
                        context = {'finish_title': 'Class Added',
                                   'user_message': 'Class Added Successfully: ' + class_display_text}
                        return render(request, 'user_message.html', RequestContext(request, context))
                    else:
                        context = {'finish_title': 'Error Adding Class',
                                   'user_message': 'Error Adding Class'}
                        return render(request, 'user_message.html', RequestContext(request, context))
                else:
                    context = {'post_to_url': '/class/add/',
                               'modal_title': 'Choose Tests For Class',
                               'first_page': False,
                               'class_add_form': class_add_form,
                               'other_classes': get_other_classes(url_prefix='/class/add/', school_pk=school_pk),
                               'allocate_tests_form': allocate_tests_form,
                               'info_load_class': 'test_instructions_load_link'}
                    return render(request, 'modal_form_add_class.html', RequestContext(request, context))
        else:
            class_add_form = (AddClassTeacherForm(teacher_pk=teacher_or_administrator.pk) if user_type == 'Teacher'
                              else AddClassForm(school_pk=school_pk))
            context = {'post_to_url': '/class/add/',
                       'modal_title': 'Enter Class Details',
                       'first_page': True,
                       'class_add_form': class_add_form,
                       'allocate_tests_form': AllocateTestsToClassForm(initialise_default=True),
                       'info_load_class': 'test_instructions_load_link'}
            return render(request, 'modal_form_add_class.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def class_adds(request):
    if request.session.get('user_type', None) == 'Administrator':
        user = User.objects.get(username=request.session.get('username', None))
        school_pk = Administrator.objects.get(user=user).school_id.pk
        if request.POST:
            class_adds_form = AddClassesForm(school_pk=school_pk, data=request.POST, files=request.FILES)
            result = class_adds_form.add_classes(request)
            if result:

                (n_created, invalid_year, teacher_username_not_exist, test_template_not_exist,
                 class_already_exists, invalid_lines, not_current_year_warning) = result

                problem_types = [(invalid_year, 'Invalid year on the following lines:'),
                                 (teacher_username_not_exist,
                                  'Could not recognise the teacher username on the following lines:'),
                                 (test_template_not_exist, 'Could not recognise the test template class on the '
                                                           'following lines:'),
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
        return reload_window_to_login(request)


def class_edit(request, class_pk, load_from_class_pk=None):
    if user_authorised_for_class(request, class_pk):
        user_type = request.session.get('user_type', None)
        user = User.objects.get(username=request.session.get('username', None))
        teacher_or_administrator = (Teacher if user_type == 'Teacher' else Administrator).objects.get(user=user)
        school_pk = teacher_or_administrator.school_id.pk
        if request.POST:
            class_edit_form = (EditClassTeacherForm(teacher_pk=teacher_or_administrator.pk, class_pk=class_pk,
                                                    data=request.POST) if user_type == 'Teacher'
                               else EditClassForm(school_pk=school_pk, class_pk=class_pk, data=request.POST))

            if load_from_class_pk:
                allocate_tests_form = AllocateEditTestsToClassForm(class_pk=class_pk,
                                                                   load_from_class_pk=load_from_class_pk)
            else:
                allocate_tests_form = AllocateEditTestsToClassForm(class_pk=class_pk, data=request.POST)

            if request.POST['button_pressed'] == 'next':
                if class_edit_form.is_valid():
                    context = {'post_to_url': '/class/edit/' + str(class_pk) + '/',
                               'modal_title': 'Choose Tests For Class',
                               'first_page': False,
                               'class_add_form': class_edit_form,
                               'other_classes': get_other_classes(url_prefix='/class/edit/' + str(class_pk) + '/',
                                                                  class_pk=class_pk),
                               'allocate_tests_form': allocate_tests_form,
                               'info_load_class': 'test_instructions_load_link'}
                    return render(request, 'modal_form_add_class.html', RequestContext(request, context))
                else:
                    context = {'post_to_url': '/class/edit/' + str(class_pk) + '/',
                               'modal_title': 'Enter Class Details',
                               'first_page': True,
                               'class_add_form': class_edit_form,
                               'allocate_tests_form': allocate_tests_form,
                               'info_load_class': 'test_instructions_load_link'}
                    return render(request, 'modal_form_add_class.html', RequestContext(request, context))
            elif request.POST['button_pressed'] == 'back':
                context = {'post_to_url': '/class/edit/' + str(class_pk) + '/',
                           'modal_title': 'Enter Class Details',
                           'first_page': True,
                           'class_add_form': class_edit_form,
                           'allocate_tests_form': allocate_tests_form,
                           'info_load_class': 'test_instructions_load_link'}
                return render(request, 'modal_form_add_class.html', RequestContext(request, context))
            else:
                if allocate_tests_form.is_valid():
                    if class_edit_form.edit_class():
                        class_instance = Class.objects.get(pk=class_pk)
                        allocate_tests_form.allocate_tests_to_class()
                        class_display_text = (class_instance.class_name + ' (' + str(class_instance.year) + ')')
                        context = {'finish_title': 'Class Edited',
                                   'user_message': 'Class Edited Successfully: ' + class_display_text}
                        return render(request, 'user_message.html', RequestContext(request, context))
                    else:
                        context = {'finish_title': 'Error Editing Class',
                                   'user_message': 'Error Editing Class'}
                        return render(request, 'user_message.html', RequestContext(request, context))
                else:
                    context = {'post_to_url': '/class/edit/' + str(class_pk) + '/',
                               'modal_title': 'Choose Tests For Class',
                               'first_page': False,
                               'class_add_form': class_edit_form,
                               'other_classes': get_other_classes(url_prefix='/class/edit/' + str(class_pk) + '/',
                                                                  class_pk=class_pk),
                               'allocate_tests_form': allocate_tests_form,
                               'info_load_class': 'test_instructions_load_link'}
                    return render(request, 'modal_form_add_class.html', RequestContext(request, context))
        else:
            class_edit_form = (EditClassTeacherForm(teacher_pk=teacher_or_administrator.pk, class_pk=class_pk)
                               if user_type == 'Teacher' else EditClassForm(school_pk=school_pk, class_pk=class_pk))
            context = {'post_to_url': '/class/edit/' + str(class_pk) + '/',
                       'modal_title': 'Enter Class Details',
                       'first_page': True,
                       'class_add_form': class_edit_form,
                       'allocate_tests_form': AllocateEditTestsToClassForm(class_pk=class_pk, initialise_default=True),
                       'info_load_class': 'test_instructions_load_link'}
            return render(request, 'modal_form_add_class.html', RequestContext(request, context))

    else:
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


def class_class(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        display_items = Class.objects.get(pk=class_pk).get_display_items()
        context = {
            'class_title': display_items[1] + ' (' + str(display_items[0]) + ') : ' + str(display_items[2]),
            'class_pk': str(class_pk),
            'class_tabs': [
                ('Results Table', '/class/results_table/' + str(class_pk), 'class_result_edit_page_load_link'),
                ('Tests Graphs', '/class/results_graphs/tests/' + str(class_pk), 'class_result_edit_page_load_link'),
                ('Students Graphs', '/class/results_graphs/students/' + str(class_pk),
                 'class_result_edit_page_load_link'),
                ('Previous Graphs', '/class/results_graphs/previous/' + str(class_pk),
                 'class_result_edit_page_load_link')
            ],
            'back_button_label': 'Back To Classes',
            'back_button_onclick_command': 'load_main_view()'
        }
        return render(request, 'class.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def class_results_table(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        class_instance = Class.objects.get(pk=class_pk)
        class_tests = [class_test.test_name for class_test in ClassTest.objects.filter(class_id=class_instance)]
        student_test_results = []
        for enrolment in StudentClassEnrolment.objects.filter(class_id=class_instance):
            if enrolment.has_pending_issues():
                approval_option = ('class_results_modal_load_link', '/class_enrolment/resolve_pending_issues/',
                                   'exclamation-sign', 'student result entry has pending issues' + '\n' +
                                                       'click to resolve issues',
                                   'attention_color')
            elif enrolment.is_approved():
                approval_option = ('class_results_modal_load_link', '/class_enrolment/un_approve/',
                                   'check', 'student result entry approved' + '\n' + 'click to remove approval',
                                   'standard_blue')
            else:
                approval_option = ('class_results_modal_load_link', '/class_enrolment/approve/',
                                   'unchecked', 'student result entry not yet approved' + '\n' + 'click to approve',
                                   'standard_blue')
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
                ('T', 'class_results_modal_load_link', '/class/test/allocate/' + str(class_pk),
                 'Change Tests For Class'),
                ('<span class="glyphicon glyphicon-print"></span>', 'test_instructions_load_link',
                 '/class/print_test_instructions/' + str(class_pk), 'Print Test Instructions', True),
                ('<span class="glyphicon glyphicon-list-alt"></span>', 'test_instructions_load_link',
                 '/class/print_student_results_sheet/' + str(class_pk), 'Print Student Results Entry Sheet', True),
                ('<span class="glyphicon glyphicon-repeat"></span>', 'modal_load_link',
                 '/class/get_new_code/' + str(class_pk), 'Reset/Get New Class Login Password', True),
                (u'\u2713', 'class_results_modal_load_link', '/class/approve_all/' + str(class_pk),
                 'Approve All Student Result Entries For Class')
            ],
            'student_test_results': student_test_results
        }
        return render(request, 'class_results_table.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def allocate_tests_to_class(request, class_pk, load_from_class_pk=None):
    if user_authorised_for_class(request, class_pk):
        if request.POST:
            allocate_test_to_class_form = AllocateEditTestsToClassForm(class_pk=class_pk, data=request.POST)
            if allocate_test_to_class_form.allocate_tests_to_class():
                context = {'finish_title': 'Tests Changed For Class',
                           'user_message': 'Tests Changed For Class Successfully'}
                return render(request, 'user_message.html', RequestContext(request, context))
            else:
                context = {'post_to_url': '/class/test/allocate/' + str(class_pk) + '/',
                           'modal_title': 'Choose Tests For Class',
                           'functionality_name': 'Change Tests',
                           'allocate_tests_form': allocate_test_to_class_form,
                           'other_classes': get_other_classes(url_prefix='/class/test/allocate/' + str(class_pk) + '/',
                                                              class_pk=class_pk),
                           'info_load_class': 'test_instructions_load_link'}
                return render(request, 'modal_form_allocate_tests.html', RequestContext(request, context))
        else:
            allocate_test_to_class_form = AllocateEditTestsToClassForm(class_pk=class_pk,
                                                                       load_from_class_pk=load_from_class_pk,
                                                                       initialise_default=True)
            context = {'post_to_url': '/class/test/allocate/' + str(class_pk) + '/',
                       'modal_title': 'Choose Tests For Class',
                       'functionality_name': 'Change Tests',
                       'allocate_tests_form': allocate_test_to_class_form,
                       'other_classes': get_other_classes(url_prefix='/class/test/allocate/' + str(class_pk) + '/',
                                                          class_pk=class_pk),
                       'info_load_class': 'test_instructions_load_link'}
            return render(request, 'modal_form_allocate_tests.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def get_other_classes(url_prefix, class_pk=None, school_pk=None):
        if class_pk:
            other_classes = (Class.objects.filter(school_id=Class.objects.get(pk=class_pk).school_id).order_by('-year').
                             exclude(pk=class_pk))
        elif school_pk:
            other_classes = Class.objects.filter(school_id=school_pk).order_by('-year')
        else:
            other_classes = []

        classes_unique = []
        for other_class in other_classes:
            other_tests = set([other_test.test_name for other_test in other_class.get_tests()])
            unique = True if other_tests else False
            classes_unique_counter = 0
            classes_unique_length = len(classes_unique)
            while unique and (classes_unique_counter < classes_unique_length):
                (class_unique, class_unique_tests) = classes_unique[classes_unique_counter]
                unique = not(class_unique_tests == other_tests)
                classes_unique_counter += 1
            if unique:
                classes_unique.append((other_class, other_tests))

        other_classes_unique = [
            (
                class_unique.class_name + '(' + str(class_unique.year) + ')', url_prefix + str(class_unique.pk) + '/'
            ) for (class_unique, class_unique_tests) in classes_unique
        ]
        other_classes_unique.insert(0, ('Default', url_prefix + 'DEFAULT/'))
        return other_classes_unique


def print_test_instructions(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        test_classes = Class.objects.get(pk=class_pk).get_tests()
        tests = []
        for test in test_classes:
            test_context = get_test_instructions_context(test.pk)
            if 'objective' in test_context.keys():
                test_tuple = (test_context['test'], test_context['heading'], test_context['objective'],
                              test_context['resources'], test_context['instructions'])
                if 'diagram' in test_context.keys():
                    test_tuple += (test_context['diagram'],)
                if 'multiple_diagrams' in test_context.keys():
                    test_tuple += (test_context['multiple_diagrams'],)
            else:
                test_tuple = (test_context['heading'])
            tests.append(test_tuple)
        context = {'title': 'Print Test Instructions', 'tests': tests}
        return render(request, 'test_instructions_print.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


def print_student_results_sheet(request, class_pk):
    if user_authorised_for_class(request, class_pk):
        class_instance = Class.objects.get(pk=class_pk)
        teacher = TeacherClassAllocation.objects.get(class_id=class_instance).teacher_id
        tests = [(class_test.test_name.test_name, class_test.test_name.percentiles.get_result_unit_text())
                 for class_test in ClassTest.objects.filter(class_id=class_pk)]
        context = {
            'class_name': class_instance.class_name + ' (' + str(class_instance.year) + ')',
            'teacher_name': teacher.first_name + " " + teacher.surname,
            'tests': tests
        }
        return render(request, 'student_results_sheet_print.html', RequestContext(request, context))
    else:
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


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
        return reload_window_to_login(request)


def class_results_graphs_tests(request, class_pk, test_pk=None):
    if user_authorised_for_class(request, class_pk):
        if (test_pk is None) or ClassTest.objects.filter(class_id=class_pk, test_name=test_pk).exists():
            context = {
                'title': 'Tests',
                'not_selected_text': 'Please Select A Test',
                'selection_options': [
                    [("/class/results_graphs/tests/" + str(class_pk) + "/" + str(class_test.test_name.pk),
                      class_test.test_name, str(class_test.test_name.pk) == str(test_pk))
                     for class_test in ClassTest.objects.filter(class_id=class_pk)]
                ]
            }
            if test_pk:
                enrolments = StudentClassEnrolment.objects.filter(class_id=class_pk, approval_status="APPROVED")
                results_for_test = []
                for enrolment in enrolments:
                    result = StudentClassTestResult.objects.filter(test=test_pk, student_class_enrolment=enrolment)
                    if result.exists():
                        results_for_test.append(result[0])
                graph_info = []
                counter = 0
                for result in results_for_test:
                    unit = result.test.percentiles.get_result_unit_text()
                    unit = "" if unit == "" else " " + unit
                    percentile = result.percentile if result.percentile else 0
                    graph_info.append((
                        counter,
                        str(result.student_class_enrolment.student_id) + " (" + result.result + unit + ")",
                        percentile
                    ))
                    counter += 1
                test_name = Test.objects.get(pk=test_pk).test_name
                graph_data = [(test_name.replace(" ", "_"), test_name, graph_info)]
                context['graphs'] = [("Class_Results", 'Class Results: ' + test_name, graph_data, 'Percentile',
                                      0, 100, 10, counter - 1, False)]
            return render(request, 'class_results_graphs.html', RequestContext(request, context))
        else:
            return reload_window_to_login(request)
    else:
        return reload_window_to_login(request)


def class_results_graphs_students(request, class_pk, student_pk=None):
    if user_authorised_for_class(request, class_pk):
        if (student_pk is None) or StudentClassEnrolment.objects.filter(class_id=class_pk,
                                                                        student_id=student_pk).exists():
            context = {
                'title': 'Students',
                'not_selected_text': 'Please Select A Student',
                'selection_options': [
                    [("/class/results_graphs/students/" + str(class_pk) + "/" + str(enrolment.student_id.pk),
                      enrolment.student_id, str(enrolment.student_id.pk) == str(student_pk))
                     for enrolment in StudentClassEnrolment.objects.filter(class_id=class_pk,
                                                                           approval_status='APPROVED')]
                ]
            }
            if student_pk:
                enrolment = StudentClassEnrolment.objects.get(class_id=class_pk, student_id=student_pk,
                                                              approval_status='APPROVED')
                results_for_student = StudentClassTestResult.objects.filter(student_class_enrolment=enrolment)
                graph_info = {}
                major_category_counter = {}
                for result in results_for_student:
                    major_category = result.test.major_test_category.major_test_category_name
                    category = result.test.test_category.test_category_name
                    if major_category not in graph_info.keys():
                        graph_info[major_category] = {}
                        major_category_counter[major_category] = 0
                    if category not in graph_info[major_category].keys():
                        graph_info[major_category][category] = []
                    unit = result.test.percentiles.get_result_unit_text()
                    unit = "" if unit == "" else " " + unit
                    percentile = result.percentile if result.percentile else 0
                    graph_info[major_category][category].append((
                        major_category_counter[major_category],
                        str(result.test.test_name) + " (" + result.result + unit + ")",
                        percentile
                    ))
                    major_category_counter[major_category] += 1
                context['graphs'] = []
                for major_category in graph_info.keys():
                    graph_data = []
                    for category in graph_info[major_category].keys():
                        graph_data.append((category.replace(" ", "_"), category, graph_info[major_category][category]))
                    context['graphs'].append((major_category.replace(" ", "_"), major_category, graph_data,
                                              'Percentile', 0, 100, 10, major_category_counter[major_category] - 1,
                                              True))
            return render(request, 'class_results_graphs.html', RequestContext(request, context))
        else:
            return reload_window_to_login(request)
    else:
        return reload_window_to_login(request)


def class_results_graphs_previous(request, class_pk, student_pk=None):
    if user_authorised_for_class(request, class_pk):
        if (student_pk is None) or StudentClassEnrolment.objects.filter(class_id=class_pk,
                                                                        student_id=student_pk).exists():
            context = {
                'title': 'Student History',
                'not_selected_text': 'Please Select A Student',
                'selection_options': [
                    [("/class/results_graphs/previous/" + str(class_pk) + "/" + str(enrolment.student_id.pk),
                      enrolment.student_id, str(enrolment.student_id.pk) == str(student_pk))
                     for enrolment in StudentClassEnrolment.objects.filter(class_id=class_pk,
                                                                           approval_status='APPROVED')]
                ]
            }
            if student_pk:
                results_for_student = []
                for enrolment in StudentClassEnrolment.objects.filter(student_id=student_pk,
                                                                      approval_status='APPROVED'):
                    for result in StudentClassTestResult.objects.filter(student_class_enrolment=enrolment):
                        results_for_student.append((enrolment.class_id.class_name, enrolment.class_id.year,
                                                    result.test.test_name,
                                                    result.test.test_category.test_category_name, result))
                for sort_index in range(4):
                    results_for_student.sort(key=itemgetter(sort_index))
                results_for_student = [result for class_name, year, test_name, test_category_name, result in
                                       results_for_student]
                graph_info = {}
                major_category_counter = {}
                for result in results_for_student:
                    major_category = result.test.major_test_category.major_test_category_name
                    category = result.test.test_category.test_category_name
                    if major_category not in graph_info.keys():
                        graph_info[major_category] = {}
                        major_category_counter[major_category] = 0
                    if category not in graph_info[major_category].keys():
                        graph_info[major_category][category] = []
                    unit = result.test.percentiles.get_result_unit_text()
                    unit = "" if unit == "" else " " + unit
                    percentile = result.percentile if result.percentile else 0
                    class_instance = result.student_class_enrolment.class_id
                    class_text_info = class_instance.class_name + " " + str(class_instance.year)
                    graph_info[major_category][category].append((
                        major_category_counter[major_category],
                        str(result.test.test_name) + ", " + class_text_info + " (" + result.result + unit + ")",
                        percentile
                    ))
                    major_category_counter[major_category] += 1
                context['graphs'] = []
                for major_category in graph_info.keys():
                    graph_data = []
                    for category in graph_info[major_category].keys():
                        graph_data.append((category.replace(" ", "_"), category, graph_info[major_category][category]))
                    context['graphs'].append((major_category.replace(" ", "_"), major_category, graph_data,
                                              'Percentile', 0, 100, 10, major_category_counter[major_category] - 1,
                                              True, True))
            return render(request, 'class_results_graphs.html', RequestContext(request, context))
        else:
            return reload_window_to_login(request)
    else:
        return reload_window_to_login(request)


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


def reload_window_to_login(request):
    context = {
        'reload_to_url': '/login',
        'alert_message': 'Your FitTest session has expired or you are not authorised to take this action.  Note you '
                         'may have logged in or logged out in another tab or window causing this session to expire.'
    }
    return render(request, 'reload_window.html', RequestContext(request, context))
