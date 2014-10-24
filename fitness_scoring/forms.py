from django import forms
from fitness_scoring.models import School, Administrator, Class, Teacher, Student, MajorTestCategory, TestCategory, Test
from fitness_scoring.models import User, TeacherClassAllocation, ClassTest, TestSet, StudentClassEnrolment
from fitness_scoring.models import StudentClassTestResult, StudentsSameName
from fitness_scoring.validators import validate_test_category_unique, validate_new_test_category_name_unique
from fitness_scoring.validators import validate_major_test_category_unique, validate_new_major_test_category_name_unique
from fitness_scoring.validators import validate_new_test_name_unique
from fitness_scoring.validators import validate_no_space, validate_file_size
from fitness_scoring.validators import is_valid_email
from fitness_scoring.fields import MultiFileField
from fitness_scoring.fileio import read_file_upload, read_test_information_from_file_upload
from fitness_scoring.user_emails import send_email_user_login
from django.core.validators import MinLengthValidator
import datetime
from datetime import date
import time


class ChangePasswordFrom(forms.Form):
    user_pk = forms.CharField(widget=forms.HiddenInput())
    old_password = forms.CharField(widget=forms.PasswordInput())
    new_password = forms.CharField(widget=forms.PasswordInput())
    new_password_again = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, user_pk, *args, **kwargs):
        super(ChangePasswordFrom, self).__init__(*args, **kwargs)

        self.fields['old_password'].error_messages = {'required': 'Please Enter Old Password'}
        self.fields['new_password'].error_messages = {'required': 'Please Enter New Password'}
        self.fields['new_password_again'].error_messages = {'required': 'Please Enter New Password Again'}

        self.fields['user_pk'].initial = user_pk

    def clean(self):
        cleaned_data = super(ChangePasswordFrom, self).clean()
        old_password = cleaned_data.get("old_password")
        new_password = cleaned_data.get("new_password")
        new_password_again = cleaned_data.get("new_password_again")
        user = User.objects.get(pk=cleaned_data.get("user_pk"))

        if old_password and new_password and new_password_again:
            if not user.authenticate_user(password=old_password):
                self._errors["old_password"] = self.error_class(['Incorrect Password'])
                del cleaned_data["old_password"]

            if new_password != new_password_again:
                error_message = 'New Passwords Do Not Match'
                self._errors["new_password"] = self.error_class([error_message])
                self._errors["new_password_again"] = self.error_class([error_message])
                del cleaned_data["new_password"]
                del cleaned_data["new_password_again"]

        return cleaned_data

    def change_password(self):
        password_changed = self.is_valid()
        if password_changed:
            user = User.objects.get(pk=self.cleaned_data['user_pk'])
            new_password = self.cleaned_data['new_password']
            user.change_password(new_password)
        return password_changed


class AddTeacherForm(forms.Form):
    school_pk = forms.CharField(widget=forms.HiddenInput())
    first_name = forms.CharField(max_length=100, required=True)
    surname = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=100, required=True, help_text='After you have added this teacher an email will '
                                                                      'be sent to them providing their login details '
                                                                      'for the system')

    def __init__(self, school_pk, *args, **kwargs):
        super(AddTeacherForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].error_messages = {'required': 'Please Enter First Name'}
        self.fields['surname'].error_messages = {'required': 'Please Enter Surname'}

        self.fields['school_pk'].initial = school_pk

        self.help_text_nl = True

    def add_teacher(self):
        if self.is_valid():
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            first_name = self.cleaned_data['first_name']
            surname = self.cleaned_data['surname']
            email = self.cleaned_data['email']
            teacher_details = Teacher.create_teacher(check_name=False, first_name=first_name,
                                                     surname=surname, school_id=school, email=email)
        else:
            teacher_details = None

        if teacher_details:
            (teacher, password) = teacher_details
            send_email_user_login(teacher.email, teacher.user.username, password, True)
        else:
            teacher = None

        return teacher


class EditTeacherForm(forms.Form):
    teacher_pk = forms.CharField(widget=forms.HiddenInput())
    school_pk = forms.CharField(widget=forms.HiddenInput())
    first_name = forms.CharField(max_length=100, required=True)
    surname = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=100, required=True)

    def __init__(self, school_pk, teacher_pk, *args, **kwargs):
        super(EditTeacherForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].error_messages = {'required': 'Please Enter First Name'}
        self.fields['surname'].error_messages = {'required': 'Please Enter Surname'}
        self.fields['email'].error_messages = {'required': 'Please Enter Email'}

        teacher = Teacher.objects.get(pk=teacher_pk)
        self.fields['teacher_pk'].initial = teacher_pk
        self.fields['school_pk'].initial = school_pk
        self.fields['first_name'].initial = teacher.first_name
        self.fields['surname'].initial = teacher.surname
        self.fields['email'].initial = teacher.email

    def edit_teacher(self):
        if self.is_valid():
            first_name = self.cleaned_data['first_name']
            surname = self.cleaned_data['surname']
            email = self.cleaned_data['email']
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            teacher = Teacher.objects.get(pk=self.cleaned_data['teacher_pk'])
            if not teacher.edit_teacher_safe(first_name=first_name, surname=surname, school_id=school, email=email):
                teacher = None
        else:
            teacher = None
        return teacher


class AddClassForm(forms.Form):
    school_pk = forms.CharField(widget=forms.HiddenInput())
    year = forms.ChoiceField()
    class_name = forms.CharField(max_length=200)
    teacher = forms.ChoiceField(required=True)

    def __init__(self, school_pk, *args, **kwargs):
        super(AddClassForm, self).__init__(*args, **kwargs)

        self.fields['class_name'].error_messages = {'required': 'Please Enter Class Name'}
        self.fields['teacher'].error_messages = {'required': 'Please Select A Teacher For The Class'}

        current_year = datetime.datetime.now().year
        self.fields['year'].choices = []
        for year in range(2000, (current_year+2)):
            self.fields['year'].choices.append((str(year), str(year)))
        self.fields['year'].initial = str(current_year)

        self.fields['teacher'].choices = [('', '')]
        for teacher in Teacher.objects.filter(school_id=School.objects.get(pk=school_pk)):
            self.fields['teacher'].choices.append((teacher.pk,
                                                   teacher.first_name + " " + teacher.surname +
                                                   " (" + teacher.user.username + ")"))
        self.fields['teacher'].initial = ''

        self.fields['school_pk'].initial = school_pk

    def clean(self):
        cleaned_data = super(AddClassForm, self).clean()
        year = cleaned_data.get("year")
        class_name = cleaned_data.get("class_name")
        teacher_pk = cleaned_data.get("teacher")
        school = School.objects.get(pk=cleaned_data.get("school_pk"))

        if year and class_name and teacher_pk:
            teacher = Teacher.objects.get(pk=teacher_pk)
            error_message = Class.create_class_errors(year=year, class_name=class_name,
                                                      school_id=school, teacher_id=teacher)
            if error_message:
                self._errors["class_name"] = self.error_class([error_message])
                del cleaned_data["year"]
                del cleaned_data["class_name"]
                del cleaned_data["teacher"]

        return cleaned_data

    def add_class(self):

        if self.is_valid():
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            year = self.cleaned_data['year']
            class_name = self.cleaned_data['class_name']
            teacher_pk = self.cleaned_data['teacher']
            teacher = Teacher.objects.get(pk=teacher_pk)
            class_saved = Class.create_class_safe(year=year, class_name=class_name,
                                                  school_id=school, teacher_id=teacher)
        else:
            class_saved = None

        return class_saved


class AddClassesForm(forms.Form):
    school_pk = forms.CharField(widget=forms.HiddenInput())
    add_classes_file = forms.FileField(required=True, validators=[validate_file_size])

    def __init__(self, school_pk, *args, **kwargs):
        super(AddClassesForm, self).__init__(*args, **kwargs)
        self.fields['add_classes_file'].error_messages = {'required': 'Please Choose Add Classes File'}

        self.fields['school_pk'].initial = school_pk

    def add_classes(self, request):
        if self.is_valid():
            result = read_file_upload(uploaded_file=request.FILES['add_classes_file'],
                                      headings=['year', 'class_name', 'teacher_username', 'test_set'])
            if result:
                (valid_lines, invalid_lines) = result
                school = School.objects.get(pk=self.cleaned_data['school_pk'])
                current_year = datetime.datetime.now().year
                n_created = 0
                teacher_username_not_exist = []
                test_set_not_exist = []
                class_already_exists = []
                not_current_year_warning = []

                for year, class_name, teacher_username, test_set_name in valid_lines:

                    if year is None:
                        year = ''
                    if class_name is None:
                        class_name = ''
                    if teacher_username is None:
                        teacher_username = ''
                    if test_set_name is None:
                        test_set_name = ''

                    user = User.objects.filter(username=teacher_username)
                    if user.exists() and Teacher.objects.filter(user=user[0], school_id=school).exists():
                        teacher = Teacher.objects.get(user=user[0])
                    else:
                        teacher = None
                        teacher_username_not_exist.append('(' + year + ', ' + class_name + ', ' + teacher_username +
                                                          ', ' + test_set_name + ')')

                    if TestSet.objects.filter(test_set_name=test_set_name, school=school).exists():
                        test_set = TestSet.objects.get(test_set_name=test_set_name, school=school)
                    elif test_set_name == '':
                        test_set = None
                    else:
                        test_set = None
                        test_set_not_exist.append('(' + year + ', ' + class_name + ', ' + teacher_username + ', ' +
                                                  test_set_name + ')')

                    if teacher and ((test_set_name == '') or test_set):
                        class_instance = Class.create_class_safe(year, class_name, school, teacher)
                        if class_instance:
                            if str(year) != str(current_year):
                                not_current_year_warning.append('(' + year + ', ' + class_name + ', ' + teacher_username
                                                                + ', ' + test_set_name + ')')
                            n_created += 1
                            if test_set:
                                class_instance.load_class_tests_from_test_set_safe(test_set.test_set_name)
                        else:
                            class_already_exists.append('(' + year + ', ' + class_name + ', ' + teacher_username +
                                                        ', ' + test_set_name + ')')

                return (n_created, teacher_username_not_exist, test_set_not_exist, class_already_exists, invalid_lines,
                        not_current_year_warning)
            else:
                return None
        else:
            return False


class EditClassForm(forms.Form):
    class_pk = forms.CharField(widget=forms.HiddenInput())
    school_pk = forms.CharField(widget=forms.HiddenInput())
    year = forms.ChoiceField()
    class_name = forms.CharField(max_length=200)
    teacher = forms.ChoiceField(required=True)

    def __init__(self, school_pk, class_pk, *args, **kwargs):
        super(EditClassForm, self).__init__(*args, **kwargs)

        self.fields['class_name'].error_messages = {'required': 'Please Enter Class Name'}
        self.fields['teacher'].error_messages = {'required': 'Please Select A Teacher For The Class'}

        current_year = datetime.datetime.now().year
        self.fields['year'].choices = []
        for year in range(2000, (current_year+2)):
            self.fields['year'].choices.append((str(year), str(year)))

        self.fields['teacher'].choices = [('', '')]
        for teacher in Teacher.objects.filter(school_id=School.objects.get(pk=school_pk)):
            self.fields['teacher'].choices.append((teacher.pk,
                                                   teacher.first_name + " " + teacher.surname +
                                                   " (" + teacher.user.username + ")"))

        class_instance = Class.objects.get(pk=class_pk)
        self.fields['class_pk'].initial = class_pk
        self.fields['school_pk'].initial = school_pk
        self.fields['year'].initial = str(class_instance.year)
        self.fields['class_name'].initial = class_instance.class_name
        if TeacherClassAllocation.objects.filter(class_id=class_instance).exists():
            self.fields['teacher'].initial = TeacherClassAllocation.objects.get(class_id=class_instance).teacher_id.pk
        else:
            self.fields['teacher'].initial = ''

    def clean(self):
        cleaned_data = super(EditClassForm, self).clean()
        year = cleaned_data.get("year")
        class_name = cleaned_data.get("class_name")
        teacher_pk = cleaned_data.get("teacher")
        class_instance = Class.objects.get(pk=cleaned_data.get("class_pk"))
        school = School.objects.get(pk=cleaned_data.get("school_pk"))

        if year and class_name and teacher_pk:
            teacher = Teacher.objects.get(pk=teacher_pk)
            error_message = class_instance.edit_class_errors(year=year, class_name=class_name,
                                                             school_id=school, teacher_id=teacher)
            if error_message:
                self._errors["class_name"] = self.error_class([error_message])
                del cleaned_data["year"]
                del cleaned_data["class_name"]
                del cleaned_data["teacher"]

        return cleaned_data

    def edit_class(self):
        class_edited = self.is_valid()
        if class_edited:
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            year = self.cleaned_data['year']
            class_name = self.cleaned_data['class_name']
            teacher_pk = self.cleaned_data['teacher']
            teacher = None if teacher_pk == '' else Teacher.objects.get(pk=teacher_pk)
            class_instance = Class.objects.get(pk=self.cleaned_data['class_pk'])
            class_edited = class_instance.edit_class_safe(year=year, class_name=class_name,
                                                          school_id=school, teacher_id=teacher)
        return class_edited


class AddClassTeacherForm(forms.Form):
    teacher_pk = forms.CharField(widget=forms.HiddenInput())
    year = forms.ChoiceField()
    class_name = forms.CharField(max_length=200)

    def __init__(self, teacher_pk, *args, **kwargs):
        super(AddClassTeacherForm, self).__init__(*args, **kwargs)

        self.fields['class_name'].error_messages = {'required': 'Please Enter Class Name'}

        current_year = datetime.datetime.now().year
        self.fields['year'].choices = []
        for year in range(2000, (current_year+2)):
            self.fields['year'].choices.append((str(year), str(year)))
        self.fields['year'].initial = str(current_year)

        self.fields['teacher_pk'].initial = teacher_pk

    def clean(self):
        cleaned_data = super(AddClassTeacherForm, self).clean()
        year = cleaned_data.get("year")
        class_name = cleaned_data.get("class_name")
        teacher = Teacher.objects.get(pk=cleaned_data.get("teacher_pk"))
        school = teacher.school_id

        if year and class_name:
            error_message = Class.create_class_errors(year=year, class_name=class_name,
                                                      school_id=school, teacher_id=teacher)
            if error_message:
                self._errors["class_name"] = self.error_class([error_message])
                del cleaned_data["year"]
                del cleaned_data["class_name"]

        return cleaned_data

    def add_class(self):

        if self.is_valid():
            teacher = Teacher.objects.get(pk=self.cleaned_data['teacher_pk'])
            school = teacher.school_id
            year = self.cleaned_data['year']
            class_name = self.cleaned_data['class_name']
            class_saved = Class.create_class_safe(year=year, class_name=class_name,
                                                  school_id=school, teacher_id=teacher)
        else:
            class_saved = None

        return class_saved


class EditClassTeacherForm(forms.Form):
    class_pk = forms.CharField(widget=forms.HiddenInput())
    teacher_pk = forms.CharField(widget=forms.HiddenInput())
    year = forms.ChoiceField()
    class_name = forms.CharField(max_length=200)

    def __init__(self, teacher_pk, class_pk, *args, **kwargs):
        super(EditClassTeacherForm, self).__init__(*args, **kwargs)

        self.fields['class_name'].error_messages = {'required': 'Please Enter Class Name'}

        current_year = datetime.datetime.now().year
        self.fields['year'].choices = []
        for year in range(2000, (current_year+2)):
            self.fields['year'].choices.append((str(year), str(year)))

        class_instance = Class.objects.get(pk=class_pk)
        self.fields['class_pk'].initial = class_pk
        self.fields['teacher_pk'].initial = teacher_pk
        self.fields['year'].initial = str(class_instance.year)
        self.fields['class_name'].initial = class_instance.class_name

    def clean(self):
        cleaned_data = super(EditClassTeacherForm, self).clean()
        year = cleaned_data.get("year")
        class_name = cleaned_data.get("class_name")
        class_instance = Class.objects.get(pk=cleaned_data.get("class_pk"))
        teacher = Teacher.objects.get(pk=cleaned_data.get("teacher_pk"))
        school = teacher.school_id

        if year and class_name:
            error_message = class_instance.edit_class_errors(year=year, class_name=class_name,
                                                             school_id=school, teacher_id=teacher)
            if error_message:
                self._errors["class_name"] = self.error_class([error_message])
                del cleaned_data["year"]
                del cleaned_data["class_name"]

        return cleaned_data

    def edit_class(self):
        class_edited = self.is_valid()
        if class_edited:
            teacher = Teacher.objects.get(pk=self.cleaned_data['teacher_pk'])
            school = teacher.school_id
            year = self.cleaned_data['year']
            class_name = self.cleaned_data['class_name']
            class_instance = Class.objects.get(pk=self.cleaned_data['class_pk'])
            class_edited = class_instance.edit_class_safe(year=year, class_name=class_name,
                                                          school_id=school, teacher_id=teacher)
        return class_edited


class AssignTestToClassForm(forms.Form):
    class_pk = forms.CharField(widget=forms.HiddenInput())
    test = forms.ChoiceField(required=True)

    def __init__(self, class_pk, *args, **kwargs):
        super(AssignTestToClassForm, self).__init__(*args, **kwargs)

        self.fields['test'].error_messages = {'required': 'Please Select Test'}

        class_instance = Class.objects.get(pk=class_pk)
        self.fields['test'].choices = []
        for test in Test.objects.all():
            if not ClassTest.objects.filter(class_id=class_instance, test_name=test):
                self.fields['test'].choices.append((test.pk, str(test)))

        self.fields['class_pk'].initial = class_pk

    def assign_test_to_class(self):
        assign_test_to_class = self.is_valid()
        if assign_test_to_class:
            class_instance = Class.objects.get(pk=self.cleaned_data['class_pk'])
            test = Test.objects.get(pk=self.cleaned_data['test'])
            assign_test_to_class = class_instance.assign_test_safe(test=test)
        return assign_test_to_class


class SaveClassTestsAsTestSetForm(forms.Form):
    class_pk = forms.CharField(widget=forms.HiddenInput())
    test_set_name = forms.CharField(max_length=300, required=True)

    def __init__(self, class_pk, *args, **kwargs):
        super(SaveClassTestsAsTestSetForm, self).__init__(*args, **kwargs)

        self.fields['test_set_name'].error_messages = {'required': 'Please Select Test Set Name'}

        self.fields['class_pk'].initial = class_pk

    def clean(self):
        cleaned_data = super(SaveClassTestsAsTestSetForm, self).clean()
        class_pk = cleaned_data.get("class_pk")
        test_set_name = cleaned_data.get("test_set_name")

        if class_pk and test_set_name:
            error_message = Class.objects.get(pk=class_pk).save_class_tests_as_test_set_errors(test_set_name)
            if error_message:
                self._errors["test_set_name"] = self.error_class([error_message])
                del cleaned_data["test_set_name"]

        return cleaned_data

    def save_class_tests_as_test_set(self):
        if self.is_valid():
            class_pk = self.cleaned_data['class_pk']
            test_set_name = self.cleaned_data['test_set_name']
            test_set = Class.objects.get(pk=class_pk).save_class_tests_as_test_set_safe(test_set_name)
        else:
            test_set = None
        return test_set


class LoadClassTestsFromTestSetForm(forms.Form):
    class_pk = forms.CharField(widget=forms.HiddenInput())
    test_set_name = forms.ChoiceField(required=True)

    def __init__(self, class_pk, *args, **kwargs):
        super(LoadClassTestsFromTestSetForm, self).__init__(*args, **kwargs)

        self.fields['test_set_name'].error_messages = {'required': 'Please Select Test Set Name'}

        self.fields['class_pk'].initial = class_pk

        self.fields['test_set_name'].choices = [('', '')]
        for test_set in TestSet.objects.filter(school_id=Class.objects.get(pk=class_pk).school_id):
            self.fields['test_set_name'].choices.append((test_set.test_set_name, test_set.test_set_name))
        self.fields['test_set_name'].initial = ''

    def clean(self):
        cleaned_data = super(LoadClassTestsFromTestSetForm, self).clean()
        class_pk = cleaned_data.get("class_pk")
        test_set_name = cleaned_data.get("test_set_name")

        if class_pk and test_set_name:
            error_message = Class.objects.get(pk=class_pk).load_class_tests_from_test_set_errors(test_set_name)
            if error_message:
                self._errors["test_set_name"] = self.error_class([error_message])
                del cleaned_data["test_set_name"]

        return cleaned_data

    def load_class_tests_from_test_set(self):
        load_valid = self.is_valid()
        if load_valid:
            class_pk = self.cleaned_data['class_pk']
            test_set_name = self.cleaned_data['test_set_name']
            load_valid = Class.objects.get(pk=class_pk).load_class_tests_from_test_set_safe(test_set_name)
        return load_valid


class AddSchoolForm(forms.Form):
    name = forms.CharField(max_length=300, required=True, validators=[MinLengthValidator(3), validate_no_space(3)])
    state = forms.ChoiceField(choices=School.STATE_CHOICES, required=True)
    subscription_paid = forms.BooleanField(initial=False, required=False)
    administrator_email = forms.EmailField(max_length=100, required=True)

    def __init__(self, *args, **kwargs):
        super(AddSchoolForm, self).__init__(*args, **kwargs)
        self.fields['name'].error_messages = {'required': 'Please Enter School Name',
                                              'min_length': 'School Name Must be at Least 3 Characters',
                                              'no_space': 'School Name Must not Have Spaces in First 3 Characters'}
        self.fields['state'].error_messages = {'required': 'Please Select A State'}
        self.fields['administrator_email'].error_messages = {'required': 'Please Enter Administrator Email'}

    def add_school(self):
        school_saved = self.is_valid()
        if school_saved:
            name = self.cleaned_data['name']
            state = self.cleaned_data['state']
            subscription_paid = self.cleaned_data['subscription_paid']
            administrator_email = self.cleaned_data['administrator_email']
            school_saved = School.create_school_and_administrator(name=name, state=state,
                                                                  subscription_paid=subscription_paid,
                                                                  administrator_email=administrator_email)
        if school_saved:
            administrator_email = self.cleaned_data['administrator_email']
            (school, administrator_password) = school_saved
            administrator_username = Administrator.objects.get(school_id=school).user.username
            send_email_user_login(administrator_email, administrator_username, administrator_password, False)
        else:
            school = None

        return school


class AddSchoolsForm(forms.Form):
    add_schools_file = forms.FileField(required=True, validators=[validate_file_size])

    def __init__(self, *args, **kwargs):
        super(AddSchoolsForm, self).__init__(*args, **kwargs)
        self.fields['add_schools_file'].error_messages = {'required': 'Please Choose Add Schools File'}

    def add_schools(self, request):
        if self.is_valid():
            result = read_file_upload(uploaded_file=request.FILES['add_schools_file'],
                                      headings=['name', 'state', 'subscription_paid', 'administrator_email'])
            if result:
                (valid_lines, invalid_lines) = result
                n_created = 0
                school_name_not_exceed_three_characters = []
                invalid_state = []
                invalid_email = []
                error_adding_school = []
                same_name_warning = []

                for name, state, subscription_paid_text, administrator_email in valid_lines:

                    if name is None:
                        name = ''
                    if state is None:
                        state = ''
                    if subscription_paid_text is None:
                        subscription_paid_text = ''
                    if administrator_email is None:
                        administrator_email = ''

                    subscription_paid = (subscription_paid_text == "Yes")

                    if len(name) < 3:
                        school_name_not_exceed_three_characters.append('(' + name + ', ' + state + ', ' +
                                                                       subscription_paid_text + ', ' +
                                                                       administrator_email + ')')
                    elif state not in [state_choice for (state_choice, state_text) in School.STATE_CHOICES]:
                        invalid_state.append('(' + name + ', ' + state + ', ' + subscription_paid_text + ', ' +
                                             administrator_email + ')')
                    elif not is_valid_email(administrator_email):
                        invalid_email.append('(' + name + ', ' + state + ', ' + subscription_paid_text + ', ' +
                                             administrator_email + ')')
                    else:

                        school_saved = School.create_school_and_administrator(name=name, state=state,
                                                                              subscription_paid=subscription_paid,
                                                                              administrator_email=administrator_email)
                        if school_saved:
                            n_created += 1
                            if len(School.objects.filter(name=name, state=state)) > 1:
                                same_name_warning.append('(' + name + ', ' + state + ', ' +
                                                         subscription_paid_text + ', ' + administrator_email + ')')

                            (school, administrator_password) = school_saved
                            administrator = Administrator.objects.get(school_id=school)
                            administrator_email = administrator.email
                            administrator_username = administrator.user.username
                            send_email_user_login(administrator_email, administrator_username, administrator_password,
                                                  False)
                        else:
                            error_adding_school.append('(' + name + ', ' + state + ', ' +
                                                       subscription_paid_text + ', ' + administrator_email + ')')

                return (n_created, school_name_not_exceed_three_characters, invalid_state, invalid_email,
                        error_adding_school, invalid_lines, same_name_warning)
            else:
                return None
        else:
            return False


class EditSchoolForm(forms.Form):
    school_pk = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=300, required=True, validators=[MinLengthValidator(3), validate_no_space(3)])
    state = forms.ChoiceField(choices=School.STATE_CHOICES, required=True)
    subscription_paid = forms.BooleanField(initial=False, required=False)
    administrator_email = forms.EmailField(max_length=100, required=True)

    def __init__(self, school_pk, *args, **kwargs):
        super(EditSchoolForm, self).__init__(*args, **kwargs)
        self.fields['name'].error_messages = {'required': 'Please Enter School Name',
                                              'min_length': 'School Name Must be at Least 3 Characters',
                                              'no_space': 'School Name Must not Have Spaces in First 3 Characters'}
        self.fields['state'].error_messages = {'required': 'Please Select A State'}
        self.fields['administrator_email'].error_messages = {'required': 'Please Enter Administrator Email'}

        school = School.objects.get(pk=school_pk)
        self.fields['school_pk'].initial = school_pk
        self.fields['name'].initial = school.name
        self.fields['state'].initial = school.state
        self.fields['subscription_paid'].initial = school.subscription_paid
        self.fields['administrator_email'].initial = Administrator.objects.get(school_id=school).email

    def edit_school(self):
        school_edited = self.is_valid()
        if school_edited:
            school_pk = self.cleaned_data['school_pk']
            name = self.cleaned_data['name']
            state = self.cleaned_data['state']
            subscription_paid = self.cleaned_data['subscription_paid']
            administrator_email = self.cleaned_data['administrator_email']
            school_editing = School.objects.get(pk=school_pk)
            school_edited = school_editing.edit_school_safe(name=name, state=state, subscription_paid=subscription_paid,
                                                            administrator_email=administrator_email)
        return school_edited


class AddMajorTestCategoryForm(forms.Form):
    major_test_category_name = forms.CharField(max_length=200, required=True,
                                               validators=[validate_major_test_category_unique])

    def __init__(self, *args, **kwargs):
        super(AddMajorTestCategoryForm, self).__init__(*args, **kwargs)
        self.fields['major_test_category_name'].error_messages = {'required': 'Please Enter Major Test Category Name'}

    def add_major_test_category(self):
        major_test_category_saved = self.is_valid()
        if major_test_category_saved:
            major_test_category_name = self.cleaned_data['major_test_category_name']
            major_test_category_saved = MajorTestCategory.create_major_test_category(major_test_category_name)
        return major_test_category_saved


class AddMajorTestCategoriesForm(forms.Form):
    add_major_test_categories_file = forms.FileField(required=True, validators=[validate_file_size])

    def __init__(self, *args, **kwargs):
        super(AddMajorTestCategoriesForm, self).__init__(*args, **kwargs)
        self.fields['add_major_test_categories_file'].error_messages = {'required': 'Please Choose Add Major Test'
                                                                                    ' Categories File'}

    def add_major_test_categories(self, request):
        if self.is_valid():
            result = read_file_upload(uploaded_file=request.FILES['add_major_test_categories_file'],
                                      headings=['major_test_category_name'])
            if result:
                (valid_lines, invalid_lines) = result
                n_created = 0
                n_blank = 0
                major_test_category_already_exist = []

                for line in valid_lines:

                    [major_test_category_name] = line

                    if (major_test_category_name is None) or (major_test_category_name == ''):
                        n_blank += 1
                    else:
                        if MajorTestCategory.create_major_test_category(
                                major_test_category_name=major_test_category_name):
                            n_created += 1
                        else:
                            major_test_category_already_exist.append(major_test_category_name)

                return n_created, n_blank, major_test_category_already_exist, invalid_lines
            else:
                return None
        else:
            return False


class EditMajorTestCategoryForm(forms.Form):
    major_test_category_pk = forms.CharField(widget=forms.HiddenInput())
    major_test_category_name = forms.CharField(max_length=200, required=True)

    def __init__(self, major_test_category_pk, *args, **kwargs):
        super(EditMajorTestCategoryForm, self).__init__(*args, **kwargs)
        self.fields['major_test_category_name'].error_messages = {'required': 'Please Enter Major Test Category Name'}

        major_test_category = MajorTestCategory.objects.get(pk=major_test_category_pk)
        self.fields['major_test_category_pk'].initial = major_test_category_pk
        self.fields['major_test_category_name'].initial = major_test_category.major_test_category_name

        self.fields['major_test_category_name'].validators = [
            validate_new_major_test_category_name_unique(major_test_category_pk=major_test_category_pk)
        ]

    def edit_major_test_category(self):
        major_test_category_edited = self.is_valid()
        if major_test_category_edited:
            major_test_category_pk = self.cleaned_data['major_test_category_pk']
            major_test_category_name = self.cleaned_data['major_test_category_name']
            major_test_category_editing = MajorTestCategory.objects.get(pk=major_test_category_pk)
            major_test_category_edited = major_test_category_editing.edit_major_test_category_safe(
                major_test_category_name=major_test_category_name)
        return major_test_category_edited


class AddTestCategoryForm(forms.Form):
    test_category_name = forms.CharField(max_length=200, required=True, validators=[validate_test_category_unique])

    def __init__(self, *args, **kwargs):
        super(AddTestCategoryForm, self).__init__(*args, **kwargs)
        self.fields['test_category_name'].error_messages = {'required': 'Please Enter Test Category Name'}

    def add_test_category(self):
        test_category_saved = self.is_valid()
        if test_category_saved:
            test_category_name = self.cleaned_data['test_category_name']
            test_category_saved = TestCategory.create_test_category(test_category_name=test_category_name)
        return test_category_saved


class AddTestCategoriesForm(forms.Form):
    add_test_categories_file = forms.FileField(required=True, validators=[validate_file_size])

    def __init__(self, *args, **kwargs):
        super(AddTestCategoriesForm, self).__init__(*args, **kwargs)
        self.fields['add_test_categories_file'].error_messages = {'required': 'Please Choose Add Test Categories File'}

    def add_test_categories(self, request):
        if self.is_valid():
            result = read_file_upload(uploaded_file=request.FILES['add_test_categories_file'],
                                      headings=['test_category_name'])
            if result:
                (valid_lines, invalid_lines) = result
                n_created = 0
                n_blank = 0
                test_category_already_exist = []

                for line in valid_lines:

                    [test_category_name] = line

                    if (test_category_name is None) or (test_category_name == ''):
                        n_blank += 1
                    else:
                        if TestCategory.create_test_category(test_category_name=test_category_name):
                            n_created += 1
                        else:
                            test_category_already_exist.append(test_category_name)

                return n_created, n_blank, test_category_already_exist, invalid_lines
            else:
                return None
        else:
            return False


class EditTestCategoryForm(forms.Form):
    test_category_pk = forms.CharField(widget=forms.HiddenInput())
    test_category_name = forms.CharField(max_length=200, required=True)

    def __init__(self, test_category_pk, *args, **kwargs):
        super(EditTestCategoryForm, self).__init__(*args, **kwargs)
        self.fields['test_category_name'].error_messages = {'required': 'Please Enter Test Category Name'}

        test_category = TestCategory.objects.get(pk=test_category_pk)
        self.fields['test_category_pk'].initial = test_category_pk
        self.fields['test_category_name'].initial = test_category.test_category_name

        self.fields['test_category_name'].validators = [
            validate_new_test_category_name_unique(test_category_pk=test_category_pk)
        ]

    def edit_test_category(self):
        test_category_edited = self.is_valid()
        if test_category_edited:
            test_category_pk = self.cleaned_data['test_category_pk']
            test_category_name = self.cleaned_data['test_category_name']
            test_category_editing = TestCategory.objects.get(pk=test_category_pk)
            test_category_edited = test_category_editing.edit_test_category_safe(test_category_name=test_category_name)
        return test_category_edited


class AddTestsForm(forms.Form):
    add_tests_files = MultiFileField(required=True)

    def __init__(self, *args, **kwargs):
        super(AddTestsForm, self).__init__(*args, **kwargs)
        self.fields['add_tests_files'].error_messages = {'required': 'Please Choose One Or More Add Test Files'}

    def add_tests(self, request):
        if self.is_valid():
            n_created = 0
            test_name_already_exists = []
            error_reading_file = []
            problems_in_files = []

            file_list = request.FILES.getlist('add_tests_files')
            for add_test_file in file_list:
                file_name = add_test_file.name
                result = read_test_information_from_file_upload(add_test_file)
                if result:
                    problems_in_data, test_information = result
                    if test_information is None:
                        problems_in_files.append((file_name, problems_in_data))
                    else:
                        (test_name, test_category, major_test_category, result_information) = test_information
                        if Test.create_test(test_name, test_category, major_test_category, result_information):
                            n_created += 1
                        else:
                            test_name_already_exists.append(file_name + ' (' + test_name + ')')
                else:
                    error_reading_file.append(file_name)
            return n_created, test_name_already_exists, error_reading_file, problems_in_files
        else:
            return False


class UpdateTestFromFileForm(forms.Form):
    test_pk = forms.CharField(widget=forms.HiddenInput())
    update_test_file = forms.FileField(required=True, validators=[validate_file_size],
                                       help_text='can only add to percentile lists cannot overwrite what is already'
                                                 ' there for an age/gender')

    def __init__(self, test_pk, *args, **kwargs):
        super(UpdateTestFromFileForm, self).__init__(*args, **kwargs)
        self.fields['update_test_file'].error_messages = {'required': 'Please Choose Update Test File'}
        self.fields['test_pk'].initial = test_pk

    def update_test(self, request):
        if self.is_valid():
            result = read_test_information_from_file_upload(request.FILES['update_test_file'])
            if result:
                (problems_in_data, test_information) = result
                error_line = None
                if test_information:
                    test = Test.objects.get(pk=self.cleaned_data['test_pk'])
                    (test_name, test_category, major_test_category, result_information) = test_information
                    (result_type, result_unit, is_upward_percentile_brackets,
                     percentile_score_conversion_type, percentile_scores) = result_information
                    if test.test_name == test_name:
                        Test.update_test(test_name, percentile_scores)
                    else:
                        error_line = 'Test names do not match'
                return problems_in_data, error_line
            else:
                return None
        else:
            return False


class EditTestForm(forms.Form):
    test_pk = forms.CharField(widget=forms.HiddenInput())
    test_name = forms.CharField(max_length=200, required=True)

    def __init__(self, test_pk, *args, **kwargs):
        super(EditTestForm, self).__init__(*args, **kwargs)

        self.fields['test_name'].error_messages = {'required': 'Please Enter Test Name'}

        test = Test.objects.get(pk=test_pk)
        self.fields['test_pk'].initial = test_pk
        self.fields['test_name'].initial = test.test_name

        self.fields['test_name'].validators = [validate_new_test_name_unique(test_pk=test_pk)]

    def edit_test(self):
        test_edited = self.is_valid()
        if test_edited:
            test_pk = self.cleaned_data['test_pk']
            test_name = self.cleaned_data['test_name']
            test_edited = Test.objects.get(pk=test_pk).edit_test_safe(test_name)
        return test_edited


class ResolveIssuesPersonalForm(forms.Form):
    resolver_type = forms.CharField(widget=forms.HiddenInput())
    enrolment_pk = forms.CharField(widget=forms.HiddenInput())
    date_tests_performed = forms.DateField(required=True, input_formats=['%d/%m/%Y'])
    student_dob = forms.DateField(required=True, input_formats=['%d/%m/%Y'])

    def __init__(self, enrolment_pk, *args, **kwargs):
        super(ResolveIssuesPersonalForm, self).__init__(*args, **kwargs)

        self.fields['resolver_type'].initial = 'solver'

        enrolment = StudentClassEnrolment.objects.get(pk=enrolment_pk)

        self.top_text_messages = ['The student age at the time the tests were performed should be between 11 and 19'
                                  ' years old', '',
                                  'The calculated age for ' + str(enrolment.student_id) + ' at the time of the tests' +
                                  ' is ' + str(enrolment.get_student_age_at_time_of_enrolment()), '',
                                  'To resolve this issue please update the date the tests were performed and/or the'
                                  ' student date of birth below:']

        self.fields['enrolment_pk'].initial = enrolment_pk
        self.fields['date_tests_performed'].initial = enrolment.enrolment_date.strftime('%d/%m/%Y')
        self.fields['student_dob'].initial = enrolment.student_id.dob.strftime('%d/%m/%Y')

        self.fields['date_tests_performed'].error_messages = {'required': 'Please Date Tests Performed',
                                                              'invalid': 'Date must be of form dd/mm/yyyy'}
        self.fields['student_dob'].error_messages = {'required': 'Please Date of Birth',
                                                     'invalid': 'Date must be of form dd/mm/yyyy'}

    def clean(self):
        cleaned_data = super(ResolveIssuesPersonalForm, self).clean()
        date_tests_performed = cleaned_data.get("date_tests_performed")
        dob = cleaned_data.get("student_dob")

        if date_tests_performed and dob:
            enrolment_age = ((date_tests_performed.year - dob.year) -
                             (1 if (date_tests_performed.month, date_tests_performed.day) < (dob.month, dob.day)
                              else 0))
            if not StudentClassEnrolment.check_enrolment_age(enrolment_age):
                error_message = ('Invalid age at time tests were performed.  This would mean that the student was ' +
                                 str(enrolment_age) + ' years old at the time of the test.')
                self._errors["date_tests_performed"] = self.error_class([error_message])
                self._errors["student_dob"] = self.error_class([error_message])
                del cleaned_data["date_tests_performed"]
                del cleaned_data["student_dob"]

        return cleaned_data

    def resolve_issues(self):
        resolved = self.is_valid()
        if resolved:
            student_dob = self.cleaned_data['student_dob']
            date_tests_performed = self.cleaned_data['date_tests_performed']
            enrolment = StudentClassEnrolment.objects.get(pk=self.cleaned_data['enrolment_pk'])
            student = enrolment.student_id
            StudentClassEnrolment.edit_student_class_enrolment_safe(
                enrolment, student_id=student.student_id, first_name=student.first_name, surname=student.surname,
                gender=student.gender, dob=student_dob, enrolment_date=date_tests_performed
            )
        return resolved


class ResolveIssuesClassForm(forms.Form):
    resolver_type = forms.CharField(widget=forms.HiddenInput())
    enrolment_results = forms.ChoiceField(required=True, widget=forms.RadioSelect)

    def __init__(self, enrolment_pk, *args, **kwargs):
        super(ResolveIssuesClassForm, self).__init__(*args, **kwargs)

        self.fields['resolver_type'].initial = 'solver'

        enrolment_clicked = StudentClassEnrolment.objects.get(pk=enrolment_pk)

        multiple_enrolments = StudentClassEnrolment.objects.filter(class_id=enrolment_clicked.class_id,
                                                                   student_id=enrolment_clicked.student_id)

        tests_string = 'Tests: '
        for test in enrolment_clicked.class_id.get_tests():
            tests_string += test.test_name + ', '
        self.top_text_messages = ['The same student cannot have multiple results for the one class', '',
                                  'Student: ' + str(enrolment_clicked.student_id) + ' has ' +
                                  str(len(multiple_enrolments)) + ' sets of results entered in class: ' +
                                  enrolment_clicked.class_id.class_name + ' (' + str(enrolment_clicked.class_id.year) +
                                  ')', '',
                                  'To resolve this issue please select the valid set of results from the options'
                                  ' below:', '',
                                  tests_string]
        self.bottom_text_messages = ['', 'WARNING: All result entries for this student other than the one selected will'
                                         ' be deleted',
                                     'If none are valid you will need to delete the last entry directly on the class'
                                     ' page']

        self.fields['enrolment_results'].choices = []
        for enrolment in multiple_enrolments:
            results_string = ''
            results = enrolment.get_test_results(text=True)
            for result in results:
                results_string += result + ', '
            self.fields['enrolment_results'].choices.append((enrolment.pk, results_string))

        self.fields['enrolment_results'].error_messages = {'required': 'Please Choose The Valid Set Of Results'}

        self.exclude_showing_label = True

    def resolve_issues(self):
        resolved = self.is_valid()
        if resolved:
            enrolment_keeping = StudentClassEnrolment.objects.get(pk=self.cleaned_data['enrolment_results'])
            enrolments = StudentClassEnrolment.objects.filter(class_id=enrolment_keeping.class_id,
                                                              student_id=enrolment_keeping.student_id)
            for enrolment in enrolments.exclude(pk=enrolment_keeping.pk):
                enrolment.delete_student_class_enrolment_safe()
        return resolved


class ResolveIssuesSchoolIDForm(forms.Form):
    resolver_type = forms.CharField(widget=forms.HiddenInput())
    resolution_options = forms.ChoiceField(required=True, widget=forms.RadioSelect)

    def __init__(self, enrolment_pk, *args, **kwargs):
        super(ResolveIssuesSchoolIDForm, self).__init__(*args, **kwargs)

        self.fields['resolver_type'].initial = 'find_solution'

        enrolment_clicked = StudentClassEnrolment.objects.get(pk=enrolment_pk)
        enrollment_same_ids = [StudentClassEnrolment.objects.filter(student_id=student)[0]
                               for student in enrolment_clicked.student_id.get_students_with_same_id()]

        self.top_text_messages = ['Two or more students cannot have the same student ID', '',
                                  'The following students have the same ID (but differ in other details):']
        self.top_text_messages += ResolveIssuesSchoolIDForm.get_text_for_student(enrolment_clicked, 1)
        student_count = 2
        for enrolment in enrollment_same_ids:
            self.top_text_messages += ResolveIssuesSchoolIDForm.get_text_for_student(enrolment, student_count)
            student_count += 1

        self.top_text_messages += ['', 'Choose one of the following possible causes of this conflict:']

        self.bottom_text_messages = ['If none of these options are a cause of this conflict than you may need to edit'
                                     ' the student result entry directly']

        choice_value = 'ChangeID:' + str(enrolment_clicked.pk)
        choice_text = ResolveIssuesSchoolIDForm.get_text_for_student_change(1)
        self.fields['resolution_options'].choices = [(choice_value, choice_text)]
        student_count = 2
        for enrolment in enrollment_same_ids:
            choice_value = 'ChangeID:' + str(enrolment.pk)
            choice_text = ResolveIssuesSchoolIDForm.get_text_for_student_change(student_count)
            self.fields['resolution_options'].choices.append((choice_value, choice_text))
            choice_value = 'From:' + str(enrolment.pk)
            choice_text = ResolveIssuesSchoolIDForm.get_text_for_student_pair(student_count, True)
            self.fields['resolution_options'].choices.append((choice_value, choice_text))
            choice_value = 'To:' + str(enrolment.pk)
            choice_text = ResolveIssuesSchoolIDForm.get_text_for_student_pair(student_count, False)
            self.fields['resolution_options'].choices.append((choice_value, choice_text))
            student_count += 1

        self.fields['resolution_options'].error_messages = {'required': 'Please Choose A Cause Of Conflict'}

        self.exclude_showing_label = True

    def find_solution(self):
        if self.is_valid():
            return self.cleaned_data['resolution_options']
        else:
            return None

    @staticmethod
    def get_text_for_student(enrolment, student_count):
        student = enrolment.student_id
        student_details = ('Student ' + str(student_count) + ':      ' + str(student) + ', ' + str(student.gender) +
                           ', born ' + student.dob.strftime('%d/%m/%Y'))
        class_instance = enrolment.class_id
        teacher = TeacherClassAllocation.objects.get(class_id=class_instance).teacher_id
        class_details = ('   (enrolled in ' + class_instance.class_name + ' (' + str(class_instance.year) +
                         '), Teacher: ' + str(teacher) + ')')
        return [student_details, class_details]

    @staticmethod
    def get_text_for_student_change(student_count):
        return 'Student ' + str(student_count) + 's student id was entered incorrectly'

    @staticmethod
    def get_text_for_student_pair(student_count_other, other_correct):
        this_student = 'Student 1'
        other_student = 'Student ' + str(student_count_other)
        correct_student = 'Student ' + str(student_count_other if other_correct else 1)
        incorrect_student = 'Student ' + str(1 if other_correct else student_count_other)
        return (this_student + ' and ' + other_student + ' are the same person and ' + correct_student +
                's details are correct and ' + incorrect_student + 's details are incorrect')


class ResolveIssuesSchoolNameForm(forms.Form):
    resolver_type = forms.CharField(widget=forms.HiddenInput())
    resolution_options = forms.ChoiceField(required=True, widget=forms.RadioSelect)

    def __init__(self, enrolment_pk, *args, **kwargs):
        super(ResolveIssuesSchoolNameForm, self).__init__(*args, **kwargs)

        self.fields['resolver_type'].initial = 'find_solution'

        enrolment_clicked = StudentClassEnrolment.objects.get(pk=enrolment_pk)
        enrollment_same_names = [StudentClassEnrolment.objects.filter(student_id=student)[0] for student in
                                 enrolment_clicked.student_id.get_students_with_same_name_not_identified()]

        self.top_text_messages = ['The following students have the same name (but differ in other details):']
        self.top_text_messages += ResolveIssuesSchoolIDForm.get_text_for_student(enrolment_clicked, 1)
        student_count = 2
        for enrolment in enrollment_same_names:
            self.top_text_messages += ResolveIssuesSchoolIDForm.get_text_for_student(enrolment, student_count)
            student_count += 1

        self.top_text_messages += ['', 'Choose one of the following options to resolve this:']

        self.bottom_text_messages = ['If none of these options are reflect the cause of this conflict than you may need'
                                     ' to edit the student result entry directly']

        choice_value = 'ChangeName:' + str(enrolment_clicked.pk)
        choice_text = ResolveIssuesSchoolNameForm.get_text_for_student_change(1)
        self.fields['resolution_options'].choices = [(choice_value, choice_text)]
        student_count = 2
        for enrolment in enrollment_same_names:
            choice_value = 'ChangeName:' + str(enrolment.pk)
            choice_text = ResolveIssuesSchoolNameForm.get_text_for_student_change(student_count)
            self.fields['resolution_options'].choices.append((choice_value, choice_text))
            choice_value = 'MarkBothNameApproval:' + str(enrolment.pk)
            choice_text = ResolveIssuesSchoolNameForm.get_text_for_student_pair_ok(student_count)
            self.fields['resolution_options'].choices.append((choice_value, choice_text))
            choice_value = 'From:' + str(enrolment.pk)
            choice_text = ResolveIssuesSchoolNameForm.get_text_for_student_pair(student_count, True)
            self.fields['resolution_options'].choices.append((choice_value, choice_text))
            choice_value = 'To:' + str(enrolment.pk)
            choice_text = ResolveIssuesSchoolNameForm.get_text_for_student_pair(student_count, False)
            self.fields['resolution_options'].choices.append((choice_value, choice_text))
            student_count += 1

        self.fields['resolution_options'].error_messages = {'required': 'Please Choose A Resolution Option'}

        self.exclude_showing_label = True

    def find_solution(self):
        if self.is_valid():
            return self.cleaned_data['resolution_options']
        else:
            return None

    @staticmethod
    def get_text_for_student_change(student_count):
        return 'Student ' + str(student_count) + 's name was entered incorrectly'

    @staticmethod
    def get_text_for_student_pair(student_count_other, other_correct):
        this_student = 'Student 1'
        other_student = 'Student ' + str(student_count_other)
        correct_student = 'Student ' + str(student_count_other if other_correct else 1)
        incorrect_student = 'Student ' + str(1 if other_correct else student_count_other)
        return (this_student + ' and ' + other_student + ' are the same person and ' + correct_student +
                's details are correct and ' + incorrect_student + 's details are incorrect')

    @staticmethod
    def get_text_for_student_pair_ok(student_count_other):
        this_student = 'Student 1'
        other_student = 'Student ' + str(student_count_other)
        return this_student + ' and ' + other_student + ' are different people and both their names are correct'


class ResolveIssuesForm(forms.Form):
    resolver_type = forms.CharField(widget=forms.HiddenInput())
    resolve_method = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, enrolment_pk, resolve_method, *args, **kwargs):
        super(ResolveIssuesForm, self).__init__(*args, **kwargs)

        self.enrolment_pk = enrolment_pk

        self.fields['resolver_type'].initial = 'solver'
        self.fields['resolve_method'].initial = resolve_method

        method, action_enrolment_pk = ResolveIssuesForm.get_resolve_method_and_pk(resolve_method)
        enrolment = StudentClassEnrolment.objects.get(pk=enrolment_pk)
        action_enrolment = StudentClassEnrolment.objects.get(pk=action_enrolment_pk)
        teacher = TeacherClassAllocation.objects.get(class_id=enrolment.class_id).teacher_id

        if (method == 'From') or (method == 'To'):
            (enrolment_from, enrolment_to) = ((enrolment, action_enrolment) if (method == 'To')
                                              else (action_enrolment, enrolment))
            self.top_text_messages = ['You have claimed that Student A and Student B should be the same person'
                                      ' and the details of Student A are correct and the details of Student B are'
                                      ' incorrect', '']
            self.top_text_messages += ResolveIssuesSchoolIDForm.get_text_for_student(enrolment_from, 'A')
            self.top_text_messages += ResolveIssuesSchoolIDForm.get_text_for_student(enrolment_to, 'B')
            if TeacherClassAllocation.objects.filter(class_id=enrolment_to.class_id, teacher_id=teacher).exists():
                self.top_text_messages += ['', 'If you go through with this action than Student Bs result entry details'
                                               ' will be changed and replaced with Student As']
                self.top_text_messages += ['', 'If you are sure you are sure you wish to take this action than click'
                                               ' the "Resolve Pending Issue" button below otherwise click "Cancel"']
                if ResolveIssuesForm.count_differences(enrolment_from.student_id, enrolment_to.student_id) >= 2:
                    self.top_text_messages += ['', 'WARNING There are a number of differences between these two'
                                                   ' students please ensure they are the same student before proceeding'
                                                   ' with this action']
                if enrolment_to.class_id != enrolment.class_id:
                    self.top_text_messages += ['', 'WARNING Just to make you aware proceeding with this action will'
                                                   ' change the details of a student result entry from another class'
                                                   ' of yours (not the current class)']
            else:
                self.top_text_messages += ['', 'This issue cannot be resolved here as it involves changing the details'
                                               ' of Student Bs result entry and not being the teacher of that class you'
                                               ' are not authorised to alter the details',
                                           'In order to resolve this issue you need to get the teacher of that class'
                                           ' or the administrator to go to the relevant class page and make the change'
                                           ' from there',
                                           'No action will occur if you press either of the "Resolve Pending Issue" or'
                                           ' "Cancel" buttons below']
        elif method == 'ChangeID':
            self.top_text_messages = ['You have claimed that the student listed below has an incorrectly entered'
                                      ' student id', '']
            self.top_text_messages += ResolveIssuesSchoolIDForm.get_text_for_student(action_enrolment, 'A')
            if TeacherClassAllocation.objects.filter(class_id=action_enrolment.class_id, teacher_id=teacher).exists():
                self.top_text_messages += ['', 'Please enter the correct student id below and click'
                                               ' "Resolve Pending Issue"']
                self.fields['student_id'] = forms.CharField(max_length=30, required=True)
                self.fields['student_id'].initial = action_enrolment.student_id.student_id
                self.fields['student_id'].error_messages = {'required': 'Please Enter New Student ID'}
                if action_enrolment.class_id != enrolment.class_id:
                    self.bottom_text_messages = ['', 'WARNING Just to make you aware proceeding with this action will'
                                                     ' change the details of a student result entry from another class'
                                                     ' of yours (not the current class)']
            else:
                self.top_text_messages += ['', 'This issue cannot be resolved here as it involves changing the details'
                                               ' of Student As result entry and not being the teacher of that class you'
                                               ' are not authorised to alter the details',
                                           'In order to resolve this issue you need to get the teacher of that class'
                                           ' or the administrator to go to the relevant class page and make the change'
                                           ' from there',
                                           'No action will occur if you press either of the "Resolve Pending Issue" or'
                                           ' "Cancel" buttons below']
        elif method == 'ChangeName':
            self.top_text_messages = ['You have claimed that the student listed below has an incorrectly entered'
                                      ' name', '']
            self.top_text_messages += ResolveIssuesSchoolIDForm.get_text_for_student(action_enrolment, 'A')
            if TeacherClassAllocation.objects.filter(class_id=action_enrolment.class_id, teacher_id=teacher).exists():
                self.top_text_messages += ['', 'Please enter the correct student name below and click'
                                               ' "Resolve Pending Issue"']
                self.fields['first_name'] = forms.CharField(max_length=100, required=True)
                self.fields['surname'] = forms.CharField(max_length=100, required=True)
                self.fields['first_name'].initial = action_enrolment.student_id.first_name
                self.fields['surname'].initial = action_enrolment.student_id.surname
                self.fields['first_name'].error_messages = {'required': 'Please Enter New First Name'}
                self.fields['surname'].error_messages = {'required': 'Please Enter New Surname'}
                if action_enrolment.class_id != enrolment.class_id:
                    self.bottom_text_messages = ['', 'WARNING Just to make you aware proceeding with this action will'
                                                     ' change the details of a student result entry from another class'
                                                     ' of yours (not the current class)']
            else:
                self.top_text_messages += ['', 'This issue cannot be resolved here as it involves changing the details'
                                               ' of Student As result entry and not being the teacher of that class you'
                                               ' are not authorised to alter the details',
                                           'In order to resolve this issue you need to get the teacher of that class'
                                           ' or the administrator to go to the relevant class page and make the change'
                                           ' from there',
                                           'No action will occur if you press either of the "Resolve Pending Issue" or'
                                           ' "Cancel" buttons below']
        elif method == 'MarkBothNameApproval':
            self.top_text_messages = ['You have claimed that the two students listed below are different people even'
                                      ' though they have the same name', '']
            self.top_text_messages += ResolveIssuesSchoolIDForm.get_text_for_student(enrolment, 'A')
            self.top_text_messages += ResolveIssuesSchoolIDForm.get_text_for_student(action_enrolment, 'B')
            self.top_text_messages += ['', 'If you are sure this is correct than click the "Resolve Pending Issue"'
                                           ' button below otherwise click "Cancel"']
            if ResolveIssuesForm.count_differences(enrolment.student_id, action_enrolment.student_id) < 2:
                    self.top_text_messages += ['', 'WARNING The two students are very similar. It seems unlikely that'
                                                   ' they are different people']
        else:
            self.top_text_messages = ['Not implemented yet, no change will occur (did not recognise method)']

    def resolve_issues(self):
        resolve_the_issue = self.is_valid()
        if resolve_the_issue:

            resolve_method = self.cleaned_data['resolve_method']
            method, action_enrolment_pk = ResolveIssuesForm.get_resolve_method_and_pk(resolve_method)
            enrolment = StudentClassEnrolment.objects.get(pk=self.enrolment_pk)
            action_enrolment = StudentClassEnrolment.objects.get(pk=action_enrolment_pk)
            teacher = TeacherClassAllocation.objects.get(class_id=enrolment.class_id).teacher_id

            if (method == 'From') or (method == 'To'):

                (enrolment_from, enrolment_to) = (
                    (enrolment, action_enrolment) if (method == 'To') else (action_enrolment, enrolment)
                )
                if TeacherClassAllocation.objects.filter(class_id=enrolment_to.class_id, teacher_id=teacher).exists():
                    student_from = enrolment_from.student_id
                    new_enrolment_date = enrolment_to.enrolment_date
                    StudentClassEnrolment.edit_student_class_enrolment_safe(
                        enrolment_to, student_id=student_from.student_id, first_name=student_from.first_name,
                        surname=student_from.surname, gender=student_from.gender, dob=student_from.dob,
                        enrolment_date=new_enrolment_date
                    )

            elif method == 'ChangeID':

                teacher_allocation = TeacherClassAllocation.objects.filter(
                    class_id=action_enrolment.class_id, teacher_id=teacher)
                if teacher_allocation.exists():
                    student = action_enrolment.student_id
                    new_enrolment_date = action_enrolment.enrolment_date
                    StudentClassEnrolment.edit_student_class_enrolment_safe(
                        action_enrolment, student_id=self.cleaned_data['student_id'], first_name=student.first_name,
                        surname=student.surname, gender=student.gender, dob=student.dob,
                        enrolment_date=new_enrolment_date
                    )

            elif method == 'ChangeName':

                teacher_allocation = TeacherClassAllocation.objects.filter(
                    class_id=action_enrolment.class_id, teacher_id=teacher)
                if teacher_allocation.exists():
                    student = action_enrolment.student_id
                    new_enrolment_date = action_enrolment.enrolment_date

                    StudentClassEnrolment.edit_student_class_enrolment_safe(
                        action_enrolment, student_id=student.student_id, first_name=self.cleaned_data['first_name'],
                        surname=self.cleaned_data['surname'], gender=student.gender, dob=student.dob,
                        enrolment_date=new_enrolment_date
                    )

            elif method == 'MarkBothNameApproval':
                StudentsSameName.identified_as_individuals_static(enrolment.student_id, action_enrolment.student_id)

        return resolve_the_issue

    @staticmethod
    def get_resolve_method_and_pk(resolve_method):
        char_index = 0
        last_possible_index = len(resolve_method) - 2
        while (resolve_method[char_index] != ':') and (char_index <= last_possible_index):
            char_index += 1
        if char_index <= last_possible_index:
            method = resolve_method[0:char_index]
            action_enrolment_pk = int(resolve_method[len(method) + 1:])
        else:
            method = None
            action_enrolment_pk = None
        return method, action_enrolment_pk

    @staticmethod
    def count_differences(student_1, student_2):
        n_differences = 0
        if student_1.student_id_lowercase != student_2.student_id_lowercase:
            n_differences += 1
        if student_1.gender != student_2.gender:
            n_differences += 1
        if student_1.dob != student_2.dob:
            n_differences += 1
        if not (((student_1.first_name_lowercase == student_2.first_name_lowercase)
                 and (student_1.surname_lowercase == student_2.surname_lowercase))
                or ((student_1.first_name_lowercase == student_2.surname_lowercase)
                and (student_1.surname_lowercase == student_2.first_name_lowercase))):
            n_differences += 1
        if ((student_1.first_name_lowercase != student_2.first_name_lowercase)
            and (student_1.surname_lowercase != student_2.surname_lowercase)
            and (student_1.first_name_lowercase != student_2.surname_lowercase)
           and (student_1.surname_lowercase != student_2.first_name_lowercase)):
            n_differences += 1
        return n_differences


class StudentEntryForm:

    def __init__(self, class_pk, data=None):
        self.class_pk = class_pk
        if data:
            self.data = data
        class_instance = Class.objects.get(pk=class_pk)
        tests = class_instance.get_tests()

        student_detail_field_description = [('text', 'Student ID', None),
                                            ('text', 'First Name', None),
                                            ('text', 'Surname', None),
                                            ('select', 'Gender', Student.GENDER_CHOICES),
                                            ('date', 'DOB', None)]
        self.student_detail_fields = []
        for field_type, label, extra in student_detail_field_description:
            name = StudentEntryForm.get_name(label)
            value = data[name] if data else None
            check_for_errors = data is not None
            choices = extra if field_type == 'select' else None
            field = StudentEntryForm.StudentDetailsField(field_type=field_type, label=label, name=name, choices=choices,
                                                         value=value, check_for_errors=check_for_errors)
            self.student_detail_fields.append(field)

        self.test_result_fields = []
        for test in tests:
            name = StudentEntryForm.get_name(test.test_name)
            value = data[name] if data else None
            check_for_errors = data is not None
            field = StudentEntryForm.ResultField(test=test, name=name, value=value, check_for_errors=check_for_errors)
            self.test_result_fields.append(field)

    def save_student_entry(self):
        is_valid = hasattr(self, 'data')
        for field in self.student_detail_fields:
            if hasattr(field, 'errors'):
                is_valid = False
        for field in self.test_result_fields:
            if hasattr(field, 'errors'):
                is_valid = False

        if is_valid:
            class_instance = Class.objects.get(pk=self.class_pk)
            student_id = None
            first_name = None
            surname = None
            gender = None
            dob = None
            for field in self.student_detail_fields:
                if field.name == 'Student_ID':
                    student_id = self.data[field.name]
                elif field.name == 'First_Name':
                    first_name = self.data[field.name]
                elif field.name == 'Surname':
                    surname = self.data[field.name]
                elif field.name == 'Gender':
                    gender = self.data[field.name]
                elif field.name == 'DOB':
                    dob = datetime.datetime.strptime(self.data[field.name], '%d/%m/%Y').date()

            enrolment = class_instance.enrol_student_safe(student_id=student_id, first_name=first_name, surname=surname,
                                                          gender=gender, dob=dob, enrolment_date=date.today())

            tests = class_instance.get_tests()
            for test in tests:
                data_label = StudentEntryForm.get_name(test.test_name)
                if self.data[data_label] is not None:
                    enrolment.enter_result_safe(test, self.data[data_label])

            return enrolment

        return None

    @staticmethod
    def get_name(label):
        name = label
        n_characters = len(name)
        for charIndex in range(0, n_characters):
            if name[charIndex] == ' ':
                name = name[0:charIndex] + '_' + name[(charIndex + 1):n_characters]
        return name

    class StudentDetailsField:

        def __init__(self, field_type, label, name, choices=None, value=None, check_for_errors=False):
            self.name = name

            if value:
                self.value = value

            if field_type == 'date':
                self.place_holder = 'dd/mm/yyyy'

            self.label_tag = '<label for="' + name + '">' + label + ':</label>'

            if (field_type == 'text') or (field_type == 'date'):
                self.html = 'input type="text" id="' + name + '" name="' + name + '"'
                if value:
                    self.html += ' value="' + value + '"'
                if hasattr(self, 'place_holder'):
                    self.html += ' placeholder="' + self.place_holder + '"'
                self.html = '<' + self.html + '>'
            elif choices:
                self.html = '<select id="' + name + '" name="' + name + '">'
                for choice_index in range(len(choices)):
                    (choice_value, option_label) = choices[choice_index]
                    self.html += '<option value="' + choice_value + '"'
                    if value:
                        if choice_value == value:
                            self.html += ' selected'
                    self.html += '>' + option_label + '</option>'
                self.html += '</select>'

            if check_for_errors:
                if value == '':
                    self.errors = 'Please enter result for ' + label
                elif field_type == 'date':
                    try:
                        datetime.datetime.strptime(value, '%d/%m/%Y')
                    except ValueError:
                        self.errors = 'Please enter date of form dd/mm/yyyy'

    class ResultField:

        def __init__(self, test, name, value=None, check_for_errors=False):
            self.name = name

            if value:
                self.value = value

            if test.percentiles.result_type == 'TIME':
                self.place_holder = 'mm:ss'

            self.label_tag = '<label for="' + name + '">' + test.test_name + ':</label>'

            self.html = 'input type="text" id="' + name + '" name="' + name + '"'
            if value:
                self.html += ' value="' + value + '"'
            if hasattr(self, 'place_holder'):
                self.html += ' placeholder="' + self.place_holder + '"'
            self.html = '<' + self.html + '>'

            self.unit_text = test.percentiles.get_result_unit_text()

            if check_for_errors:
                if value == '':
                    self.errors = 'Please enter result for ' + test.test_name
                elif test.percentiles.result_type == 'DOUBLE':
                    try:
                        float(value)
                    except ValueError:
                        self.errors = 'Please enter a decimal value for ' + test.test_name
                elif test.percentiles.result_type == 'TIME':
                    try:
                        time.strptime(value, '%M:%S')
                    except ValueError:
                        self.errors = 'Please enter a time value of the form mm:ss for ' + test.test_name
                elif test.percentiles.result_type == 'INTEGER':
                    try:
                        if int(value) != float(value):
                            self.errors = 'Please enter a whole number value for ' + test.test_name
                    except ValueError:
                        self.errors = 'Please enter a whole number value for ' + test.test_name


class StudentEntryEditForm:

    def __init__(self, enrolment_pk, data=None):
        self.enrolment_pk = enrolment_pk
        if data:
            self.data = data
        enrolment = StudentClassEnrolment.objects.get(pk=enrolment_pk)
        tests = enrolment.class_id.get_tests()

        student_detail_field_description = [('text', 'Student ID', None),
                                            ('text', 'First Name', None),
                                            ('text', 'Surname', None),
                                            ('select', 'Gender', Student.GENDER_CHOICES),
                                            ('date', 'DOB', None)]
        self.student_detail_fields = []
        for field_type, label, extra in student_detail_field_description:
            name = StudentEntryForm.get_name(label)
            if data:
                value = data[name]
            else:
                if label == 'Student ID':
                    value = enrolment.student_id.student_id
                elif label == 'First Name':
                    value = enrolment.student_id.first_name
                elif label == 'Surname':
                    value = enrolment.student_id.surname
                elif label == 'Gender':
                    value = enrolment.student_id.gender
                elif label == 'DOB':
                    value = enrolment.student_id.dob.strftime('%d/%m/%Y')
                else:
                    value = None
            check_for_errors = data is not None
            choices = extra if field_type == 'select' else None
            field = StudentEntryForm.StudentDetailsField(field_type=field_type, label=label, name=name, choices=choices,
                                                         value=value, check_for_errors=check_for_errors)
            self.student_detail_fields.append(field)

        self.test_result_fields = []
        for test in tests:
            name = StudentEntryForm.get_name(test.test_name)
            if data:
                value = data[name]
            else:
                if StudentClassTestResult.objects.filter(student_class_enrolment=enrolment, test=test).exists():
                    value = StudentClassTestResult.objects.get(student_class_enrolment=enrolment, test=test).result
                else:
                    value = None
            check_for_errors = data is not None
            field = StudentEntryForm.ResultField(test=test, name=name, value=value, check_for_errors=check_for_errors)
            self.test_result_fields.append(field)

        date_of_enrolment_label = 'Date Tests Were Performed'
        date_of_enrolment_name = StudentEntryForm.get_name(date_of_enrolment_label)
        if data:
            value = data[date_of_enrolment_name]
        else:
            value = enrolment.enrolment_date.strftime('%d/%m/%Y')
        self.extra_fields = [StudentEntryEditForm.DateOfEnrolmentField(date_of_enrolment_label, date_of_enrolment_name,
                                                                       value, data is not None)]

    def edit_student_entry(self):
        is_valid = hasattr(self, 'data')
        for field in self.student_detail_fields:
            if hasattr(field, 'errors'):
                is_valid = False
        for field in self.test_result_fields:
            if hasattr(field, 'errors'):
                is_valid = False
        for field in self.extra_fields:
            if hasattr(field, 'errors'):
                is_valid = False

        if is_valid:
            enrolment = StudentClassEnrolment.objects.get(pk=self.enrolment_pk)
            student_id = None
            first_name = None
            surname = None
            gender = None
            dob = None
            for field in self.student_detail_fields:
                if field.name == 'Student_ID':
                    student_id = self.data[field.name]
                elif field.name == 'First_Name':
                    first_name = self.data[field.name]
                elif field.name == 'Surname':
                    surname = self.data[field.name]
                elif field.name == 'Gender':
                    gender = self.data[field.name]
                elif field.name == 'DOB':
                    dob = datetime.datetime.strptime(self.data[field.name], '%d/%m/%Y').date()

            class_instance = enrolment.class_id
            student_old = enrolment.student_id
            tests = class_instance.get_tests()
            new_enrolment_date = datetime.datetime.strptime(self.data['Date_Tests_Were_Performed'], '%d/%m/%Y').date()

            if ((student_old.student_id != student_id) or (student_old.first_name != first_name) or
                    (student_old.surname != surname) or (student_old.gender != gender) or (student_old.dob != dob) or
                    (enrolment.enrolment_date != new_enrolment_date)):

                enrolment = StudentClassEnrolment.edit_student_class_enrolment_safe(
                    enrolment=enrolment, student_id=student_id, first_name=first_name, surname=surname, gender=gender,
                    dob=dob, enrolment_date=new_enrolment_date
                )

            for test in tests:
                data_label = StudentEntryForm.get_name(test.test_name)
                result = self.data[data_label]
                if result is not None:
                    test_result = StudentClassTestResult.objects.filter(student_class_enrolment=enrolment, test=test)
                    if not test_result.exists():
                        enrolment.enter_result_safe(test, result)
                    elif test_result[0].result != result:
                        enrolment.edit_result_safe(test, result)

        return is_valid

    class DateOfEnrolmentField:

        def __init__(self, label, name, value, check_for_errors=False):

            self.name = name
            self.value = value
            self.place_holder = 'dd/mm/yyyy'

            self.label_tag = '<label for="' + name + '">' + label + ':</label>'

            self.html = 'input type="text" id="' + name + '" name="' + name + '"'
            self.html += ' value="' + value + '"'
            self.html += ' placeholder="' + self.place_holder + '"'
            self.html = '<' + self.html + '>'

            if check_for_errors:
                if value == '':
                    self.errors = 'Please enter result for ' + label
                else:
                    try:
                        datetime.datetime.strptime(value, '%d/%m/%Y')
                    except ValueError:
                        self.errors = 'Please enter date of form dd/mm/yyyy'