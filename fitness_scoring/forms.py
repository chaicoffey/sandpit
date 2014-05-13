from django import forms
from fitness_scoring.models import School, Administrator, Class, Teacher, TestCategory, Test, User
from fitness_scoring.models import TeacherClassAllocation, ClassTest, TestSet
from fitness_scoring.validators import validate_school_unique, validate_new_school_name_unique
from fitness_scoring.validators import validate_test_category_unique, validate_new_test_category_name_unique
from fitness_scoring.validators import validate_new_test_name_unique
from fitness_scoring.validators import validate_no_space
from fitness_scoring.fields import MultiFileField
from fitness_scoring.fileio import add_schools_from_file_upload, add_test_categories_from_file_upload
from fitness_scoring.fileio import add_test_from_file_upload, update_test_from_file_upload
from fitness_scoring.fileio import read_classes_file_upload
from pe_site.settings import DEFAULT_FROM_EMAIL
from django.core.validators import MinLengthValidator
import datetime
from django.core.mail import send_mail


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
    email = forms.EmailField(max_length=100, required=True)

    def __init__(self, school_pk, *args, **kwargs):
        super(AddTeacherForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].error_messages = {'required': 'Please Enter First Name'}
        self.fields['surname'].error_messages = {'required': 'Please Enter Surname'}

        self.fields['school_pk'].initial = school_pk

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

            message = ('username: ' + teacher.user.username + '\n' +
                       'password: ' + password)
            send_mail('Fitness Testing App - Teacher Login Details', message, DEFAULT_FROM_EMAIL, [teacher.email])
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
    add_classes_file = forms.FileField(required=True)

    def __init__(self, school_pk, *args, **kwargs):
        super(AddClassesForm, self).__init__(*args, **kwargs)
        self.fields['add_classes_file'].error_messages = {'required': 'Please Choose Add Classes File'}

        self.fields['school_pk'].initial = school_pk

    def add_classes(self, request):
        if self.is_valid():

            (valid_lines, invalid_lines) = read_classes_file_upload(uploaded_file=request.FILES['add_classes_file'])
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            n_created = 0
            teacher_username_not_exist = []
            test_set_not_exist = []
            class_already_exists = []

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
                    teacher_username_not_exist.append('(' + year + ', ' + class_name + ', ' + teacher_username + ', ' +
                                                      test_set_name + ')')

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
                        n_created += 1
                        if test_set:
                            class_instance.load_class_tests_from_test_set_safe(test_set.test_set_name)
                    else:
                        class_already_exists.append('(' + year + ', ' + class_name + ', ' + teacher_username + ', ' +
                                                    test_set_name + ')')

            return n_created, teacher_username_not_exist, test_set_not_exist, class_already_exists, invalid_lines
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
    name = forms.CharField(max_length=300, required=True, validators=[MinLengthValidator(3), validate_no_space(3),
                                                                      validate_school_unique])
    subscription_paid = forms.BooleanField(initial=False, required=False)
    administrator_email = forms.EmailField(max_length=100, required=True)

    def __init__(self, *args, **kwargs):
        super(AddSchoolForm, self).__init__(*args, **kwargs)
        self.fields['name'].error_messages = {'required': 'Please Enter School Name',
                                              'min_length': 'School Name Must be at Least 3 Characters',
                                              'no_space': 'School Name Must not Have Spaces in First 3 Characters'}
        self.fields['administrator_email'].error_messages = {'required': 'Please Enter Administrator Email'}

    def add_school(self):
        school_saved = self.is_valid()
        if school_saved:
            name = self.cleaned_data['name']
            subscription_paid = self.cleaned_data['subscription_paid']
            administrator_email = self.cleaned_data['administrator_email']
            school_saved = School.create_school_and_administrator(name=name, subscription_paid=subscription_paid,
                                                                  administrator_email=administrator_email)
        if school_saved:
            administrator_email = self.cleaned_data['administrator_email']
            (school, administrator_password) = school_saved
            administrator_username = Administrator.objects.get(school_id=school).user.username

            message = ('username: ' + administrator_username + '\n' +
                       'password: ' + administrator_password)
            send_mail('Fitness Testing App - Administrator Login Details', message, DEFAULT_FROM_EMAIL,
                      [administrator_email])
        else:
            school = None

        return school


class AddSchoolsForm(forms.Form):
    add_schools_file = forms.FileField(required=True)

    def __init__(self, *args, **kwargs):
        super(AddSchoolsForm, self).__init__(*args, **kwargs)
        self.fields['add_schools_file'].error_messages = {'required': 'Please Choose Add Schools File'}

    def add_schools(self, request):
        if self.is_valid():
            (administrator_details,
             n_updated, n_not_created_or_updated) = add_schools_from_file_upload(request.FILES['add_schools_file'])
            for school, administrator_password in administrator_details:
                administrator = Administrator.objects.get(school_id=school)
                administrator_email = administrator.email
                administrator_username = administrator.user.username
                message = ('username: ' + administrator_username + '\n' +
                           'password: ' + administrator_password)
                send_mail('Fitness Testing App - Administrator Login Details', message, DEFAULT_FROM_EMAIL,
                          [administrator_email])
            return len(administrator_details), n_updated, n_not_created_or_updated
        else:
            return False


class EditSchoolForm(forms.Form):
    school_pk = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=300, required=True, validators=[MinLengthValidator(3), validate_no_space(3)])
    subscription_paid = forms.BooleanField(initial=False, required=False)
    administrator_email = forms.EmailField(max_length=100, required=True)

    def __init__(self, school_pk, *args, **kwargs):
        super(EditSchoolForm, self).__init__(*args, **kwargs)
        self.fields['name'].error_messages = {'required': 'Please Enter School Name',
                                              'min_length': 'School Name Must be at Least 3 Characters',
                                              'no_space': 'School Name Must not Have Spaces in First 3 Characters'}
        self.fields['administrator_email'].error_messages = {'required': 'Please Enter Administrator Email'}

        school = School.objects.get(pk=school_pk)
        self.fields['school_pk'].initial = school_pk
        self.fields['name'].initial = school.name
        self.fields['subscription_paid'].initial = school.subscription_paid
        self.fields['administrator_email'].initial = Administrator.objects.get(school_id=school).email

        self.fields['name'].validators = [validate_new_school_name_unique(school_pk=school_pk)]

    def edit_school(self):
        school_edited = self.is_valid()
        if school_edited:
            school_pk = self.cleaned_data['school_pk']
            name = self.cleaned_data['name']
            subscription_paid = self.cleaned_data['subscription_paid']
            administrator_email = self.cleaned_data['administrator_email']
            school_editing = School.objects.get(pk=school_pk)
            school_edited = school_editing.edit_school_safe(name=name, subscription_paid=subscription_paid,
                                                            administrator_email=administrator_email)
        return school_edited


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
    add_test_categories_file = forms.FileField(required=True)

    def __init__(self, *args, **kwargs):
        super(AddTestCategoriesForm, self).__init__(*args, **kwargs)
        self.fields['add_test_categories_file'].error_messages = {'required': 'Please Choose Add Test Categories File'}

    def add_test_categories(self, request):
        if self.is_valid():
            return add_test_categories_from_file_upload(request.FILES['add_test_categories_file'])
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
            n_not_created = 0
            file_list = request.FILES.getlist('add_tests_files')
            for add_test_file in file_list:
                if add_test_from_file_upload(add_test_file):
                    n_created += 1
                else:
                    n_not_created += 1
            result = (n_created, n_not_created)
        else:
            result = None
        return result


class UpdateTestFromFileForm(forms.Form):
    test_pk = forms.CharField(widget=forms.HiddenInput())
    update_test_file = forms.FileField(required=True, help_text='can only add to percentile lists cannot overwrite what'
                                                                ' is already there for an age/gender')

    def __init__(self, test_pk, *args, **kwargs):
        super(UpdateTestFromFileForm, self).__init__(*args, **kwargs)
        self.fields['update_test_file'].error_messages = {'required': 'Please Choose Update Test File'}
        self.fields['test_pk'].initial = test_pk

    def update_test(self, request):
        if self.is_valid():
            test = Test.objects.get(pk=self.cleaned_data['test_pk'])
            return update_test_from_file_upload(request.FILES['update_test_file'], test)
        else:
            return None


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