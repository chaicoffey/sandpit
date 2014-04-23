from django import forms
from fitness_scoring.models import Student, School, Class, Teacher, TestCategory, Test
from fitness_scoring.models import TeacherClassAllocation, StudentClassEnrolment
from fitness_scoring.validators import validate_school_unique, validate_new_school_name_unique
from fitness_scoring.validators import validate_test_category_unique, validate_new_test_category_name_unique
from fitness_scoring.validators import validate_test_unique, validate_new_test_name_unique
from fitness_scoring.validators import validate_student_unique, validate_new_student_id_unique
from fitness_scoring.validators import validate_no_space, validate_date_field
from fitness_scoring.fileio import add_schools_from_file_upload, add_test_categories_from_file_upload
from fitness_scoring.fileio import add_tests_from_file_upload, add_students_from_file_upload
from fitness_scoring.fileio import add_teachers_from_file_upload, add_classes_from_file_upload
from fitness_scoring.fileio import enrol_students_in_class_from_file_upload
from django.core.validators import MinLengthValidator
import datetime


class AddStudentForm(forms.Form):
    student_id = forms.CharField(max_length=30, required=True)
    school_pk = forms.CharField(widget=forms.HiddenInput())
    first_name = forms.CharField(max_length=100, required=True)
    surname = forms.CharField(max_length=100, required=True)
    gender = forms.ChoiceField(choices=Student.GENDER_CHOICES, required=True)
    dob = forms.CharField(required=True, help_text='(dd/mm/yyyy)', validators=[validate_date_field('%d/%m/%Y')])

    def __init__(self, school_pk, *args, **kwargs):
        super(AddStudentForm, self).__init__(*args, **kwargs)

        self.fields['student_id'].error_messages = {'required': 'Please Enter Student ID'}
        self.fields['first_name'].error_messages = {'required': 'Please Enter First Name'}
        self.fields['surname'].error_messages = {'required': 'Please Enter Surname'}
        self.fields['gender'].error_messages = {'required': 'Please Select A Gender'}
        self.fields['dob'].error_messages = {'required': 'Please Enter Date Of Birth',
                                             'date_format': 'Date Of Birth Should Be Of Form dd/mm/yyyy'}

        self.fields['school_pk'].initial = school_pk

        self.fields['student_id'].validators = [validate_student_unique(school_pk)]

    def add_student(self):
        student_saved = self.is_valid()
        if student_saved:
            student_id = self.cleaned_data['student_id']
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            first_name = self.cleaned_data['first_name']
            surname = self.cleaned_data['surname']
            gender = self.cleaned_data['gender']
            dob = datetime.datetime.strptime(self.cleaned_data['dob'], '%d/%m/%Y')
            student_saved = Student.create_student(check_name=False, student_id=student_id, school_id=school,
                                                   first_name=first_name, surname=surname, gender=gender, dob=dob)
        return student_saved


class AddStudentsForm(forms.Form):
    school_pk = forms.CharField(widget=forms.HiddenInput())
    add_students_file = forms.FileField(required=True)

    def __init__(self, school_pk, *args, **kwargs):
        super(AddStudentsForm, self).__init__(*args, **kwargs)
        self.fields['add_students_file'].error_messages = {'required': 'Please Choose Add Students File'}

        self.fields['school_pk'].initial = school_pk

    def add_students(self, request):
        if self.is_valid():
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            return add_students_from_file_upload(uploaded_file=request.FILES['add_students_file'], school_id=school)
        else:
            return False


class EditStudentForm(forms.Form):
    student_pk = forms.CharField(widget=forms.HiddenInput())
    school_pk = forms.CharField(widget=forms.HiddenInput())
    student_id = forms.CharField(max_length=30, required=True)
    first_name = forms.CharField(max_length=100, required=True)
    surname = forms.CharField(max_length=100, required=True)
    gender = forms.ChoiceField(choices=Student.GENDER_CHOICES, required=True)
    dob = forms.CharField(required=True, help_text='(dd/mm/yyyy)', validators=[validate_date_field('%d/%m/%Y')])

    def __init__(self, school_pk, student_pk, *args, **kwargs):
        super(EditStudentForm, self).__init__(*args, **kwargs)

        self.fields['student_id'].error_messages = {'required': 'Please Enter Student ID'}
        self.fields['first_name'].error_messages = {'required': 'Please Enter First Name'}
        self.fields['surname'].error_messages = {'required': 'Please Enter Surname'}
        self.fields['gender'].error_messages = {'required': 'Please Select A Gender'}
        self.fields['dob'].error_messages = {'required': 'Please Enter Date Of Birth',
                                             'date_format': 'Date Of Birth Should Be Of Form dd/mm/yyyy'}

        student = Student.objects.get(pk=student_pk)
        self.fields['student_pk'].initial = student_pk
        self.fields['school_pk'].initial = school_pk
        self.fields['student_pk'].initial = student_pk
        self.fields['student_id'].initial = student.student_id
        self.fields['first_name'].initial = student.first_name
        self.fields['surname'].initial = student.surname
        self.fields['gender'].initial = student.gender
        self.fields['dob'].initial = student.dob.strftime('%d/%m/%Y')

        self.fields['student_id'].validators = [validate_new_student_id_unique(student_pk=student_pk,
                                                                               school_pk=school_pk)]

    def edit_student(self):
        student_edited = self.is_valid()
        if student_edited:
            student_id = self.cleaned_data['student_id']
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            first_name = self.cleaned_data['first_name']
            surname = self.cleaned_data['surname']
            gender = self.cleaned_data['gender']
            dob = datetime.datetime.strptime(self.cleaned_data['dob'], '%d/%m/%Y')
            student_editing = Student.objects.get(pk=self.cleaned_data['student_pk'])
            student_edited = student_editing.edit_student_safe(student_id=student_id, school_id=school,
                                                               first_name=first_name, surname=surname,
                                                               gender=gender, dob=dob)
        return student_edited


class AddTeacherForm(forms.Form):
    school_pk = forms.CharField(widget=forms.HiddenInput())
    first_name = forms.CharField(max_length=100, required=True)
    surname = forms.CharField(max_length=100, required=True)

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
            teacher = Teacher.create_teacher(check_name=False, first_name=first_name, surname=surname, school_id=school)
        else:
            teacher = None
        return teacher


class AddTeachersForm(forms.Form):
    school_pk = forms.CharField(widget=forms.HiddenInput())
    add_teachers_file = forms.FileField(required=True)

    def __init__(self, school_pk, *args, **kwargs):
        super(AddTeachersForm, self).__init__(*args, **kwargs)
        self.fields['add_teachers_file'].error_messages = {'required': 'Please Choose Add Teachers File'}

        self.fields['school_pk'].initial = school_pk

    def add_teachers(self, request):
        if self.is_valid():
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            return add_teachers_from_file_upload(uploaded_file=request.FILES['add_teachers_file'], school_id=school)
        else:
            return False


class EditTeacherForm(forms.Form):
    teacher_pk = forms.CharField(widget=forms.HiddenInput())
    school_pk = forms.CharField(widget=forms.HiddenInput())
    first_name = forms.CharField(max_length=100, required=True)
    surname = forms.CharField(max_length=100, required=True)

    def __init__(self, school_pk, teacher_pk, *args, **kwargs):
        super(EditTeacherForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].error_messages = {'required': 'Please Enter First Name'}
        self.fields['surname'].error_messages = {'required': 'Please Enter Surname'}

        teacher = Teacher.objects.get(pk=teacher_pk)
        self.fields['teacher_pk'].initial = teacher_pk
        self.fields['school_pk'].initial = school_pk
        self.fields['first_name'].initial = teacher.first_name
        self.fields['surname'].initial = teacher.surname

    def edit_teacher(self):
        if self.is_valid():
            first_name = self.cleaned_data['first_name']
            surname = self.cleaned_data['surname']
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            teacher = Teacher.objects.get(pk=self.cleaned_data['teacher_pk'])
            if not teacher.edit_teacher_safe(first_name=first_name, surname=surname, school_id=school):
                teacher = None
        else:
            teacher = None
        return teacher


class AddClassForm(forms.Form):
    school_pk = forms.CharField(widget=forms.HiddenInput())
    year = forms.ChoiceField()
    class_name = forms.CharField(max_length=200)
    teacher = forms.ChoiceField(required=False)

    def __init__(self, school_pk, *args, **kwargs):
        super(AddClassForm, self).__init__(*args, **kwargs)

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
        school = School.objects.get(pk=cleaned_data.get("school_pk"))

        if year and class_name:
            if Class.objects.filter(year=year, class_name=class_name, school_id=school).exists():
                self._errors["class_name"] = self.error_class(['Class Already Exists: ' + class_name +
                                                               '(' + year + ')'])
                del cleaned_data["school_pk"]
                del cleaned_data["year"]
                del cleaned_data["class_name"]
                del cleaned_data["teacher"]

        return cleaned_data

    def add_class(self):
        class_saved = self.is_valid()
        if class_saved:
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            year = self.cleaned_data['year']
            class_name = self.cleaned_data['class_name']
            teacher_pk = self.cleaned_data['teacher']
            teacher = None if teacher_pk == '' else Teacher.objects.get(pk=teacher_pk)
            class_saved = Class.create_class(year=year, class_name=class_name, school_id=school, teacher_id=teacher)
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
            school = School.objects.get(pk=self.cleaned_data['school_pk'])
            return add_classes_from_file_upload(uploaded_file=request.FILES['add_classes_file'], school_id=school)
        else:
            return False


class EditClassForm(forms.Form):
    class_pk = forms.CharField(widget=forms.HiddenInput())
    school_pk = forms.CharField(widget=forms.HiddenInput())
    year = forms.ChoiceField()
    class_name = forms.CharField(max_length=200)
    teacher = forms.ChoiceField(required=False)

    def __init__(self, school_pk, class_pk, *args, **kwargs):
        super(EditClassForm, self).__init__(*args, **kwargs)

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
        class_instance = Class.objects.get(pk=cleaned_data.get("class_pk"))
        school = School.objects.get(pk=cleaned_data.get("school_pk"))

        if year and class_name:
            if ((class_instance.class_name != class_name) or (str(class_instance.year) != year)) and\
                    Class.objects.filter(year=year, class_name=class_name, school_id=school).exists():
                self._errors["class_name"] = self.error_class(['Class Already Exists: ' + class_name +
                                                               ' (' + year + ')'])
                del cleaned_data["school_pk"]
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


class EnrolStudentInClassForm(forms.Form):
    class_pk = forms.CharField(widget=forms.HiddenInput())
    student = forms.ChoiceField(required=True)

    def __init__(self, class_pk, *args, **kwargs):
        super(EnrolStudentInClassForm, self).__init__(*args, **kwargs)

        self.fields['student'].error_messages = {'required': 'Please Select Student'}

        class_instance = Class.objects.get(pk=class_pk)
        self.fields['student'].choices = []
        for student in Student.objects.filter(school_id=class_instance.school_id):
            if not StudentClassEnrolment.objects.filter(class_id=class_instance, student_id=student):
                self.fields['student'].choices.append((student.pk, str(student)))

        self.fields['class_pk'].initial = class_pk

    def enrol_student_in_class(self):
        enrol_student_in_class = self.is_valid()
        if enrol_student_in_class:
            class_instance = Class.objects.get(pk=self.cleaned_data['class_pk'])
            student = Student.objects.get(pk=self.cleaned_data['student'])
            enrol_student_in_class = class_instance.enrol_student_safe(student=student)
        return enrol_student_in_class


class EnrolStudentsInClassForm(forms.Form):
    class_pk = forms.CharField(widget=forms.HiddenInput())
    add_students_to_class_file = forms.FileField(required=True)

    def __init__(self, class_pk, *args, **kwargs):
        super(EnrolStudentsInClassForm, self).__init__(*args, **kwargs)

        self.fields['add_students_to_class_file'].error_messages = {'required': 'Please Select Add Students'
                                                                                ' To Classes File'}

        self.fields['class_pk'].initial = class_pk

    def enrol_students_in_class(self, request):
        if self.is_valid():
            class_instance = Class.objects.get(pk=self.cleaned_data['class_pk'])
            uploaded_file = request.FILES['add_students_to_class_file']
            return enrol_students_in_class_from_file_upload(uploaded_file=uploaded_file, class_instance=class_instance)
        else:
            return False


class AddSchoolForm(forms.Form):
    name = forms.CharField(max_length=300, required=True, validators=[MinLengthValidator(3), validate_no_space(3),
                                                                      validate_school_unique])
    subscription_paid = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super(AddSchoolForm, self).__init__(*args, **kwargs)
        self.fields['name'].error_messages = {'required': 'Please Enter School Name',
                                              'min_length': 'School Name Must be at Least 3 Characters',
                                              'no_space': 'School Name Must not Have Spaces in First 3 Characters'}

    def add_school(self):
        school_saved = self.is_valid()
        if school_saved:
            name = self.cleaned_data['name']
            subscription_paid = self.cleaned_data['subscription_paid']
            school_saved = School.create_school_and_administrator(name=name, subscription_paid=subscription_paid)
        return school_saved


class AddSchoolsForm(forms.Form):
    add_schools_file = forms.FileField(required=True)

    def __init__(self, *args, **kwargs):
        super(AddSchoolsForm, self).__init__(*args, **kwargs)
        self.fields['add_schools_file'].error_messages = {'required': 'Please Choose Add Schools File'}

    def add_schools(self, request):
        if self.is_valid():
            return add_schools_from_file_upload(request.FILES['add_schools_file'])
        else:
            return False


class EditSchoolForm(forms.Form):
    school_pk = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=300, required=True, validators=[MinLengthValidator(3), validate_no_space(3)])
    subscription_paid = forms.BooleanField(initial=False, required=False)

    def __init__(self, school_pk, *args, **kwargs):
        super(EditSchoolForm, self).__init__(*args, **kwargs)
        self.fields['name'].error_messages = {'required': 'Please Enter School Name',
                                              'min_length': 'School Name Must be at Least 3 Characters',
                                              'no_space': 'School Name Must not Have Spaces in First 3 Characters'}

        school = School.objects.get(pk=school_pk)
        self.fields['school_pk'].initial = school_pk
        self.fields['name'].initial = school.name
        self.fields['subscription_paid'].initial = school.subscription_paid

        self.fields['name'].validators = [validate_new_school_name_unique(school_pk=school_pk)]

    def edit_school(self):
        school_edited = self.is_valid()
        if school_edited:
            school_pk = self.cleaned_data['school_pk']
            name = self.cleaned_data['name']
            subscription_paid = self.cleaned_data['subscription_paid']
            school_editing = School.objects.get(pk=school_pk)
            school_edited = school_editing.edit_school_safe(name=name, subscription_paid=subscription_paid)
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


class AddTestForm(forms.Form):
    test_name = forms.CharField(max_length=200, required=True, validators=[validate_test_unique])
    test_category = forms.ChoiceField(required=True)
    description = forms.CharField(widget=forms.Textarea(), max_length=400, required=True)
    result_type = forms.ChoiceField(required=True, choices=Test.RESULT_TYPE_CHOICES)
    is_upward_percentile_brackets = forms.BooleanField(required=False, initial=True)
    percentile_score_conversion_type = forms.ChoiceField(required=True,
                                                         choices=Test.PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES)

    def __init__(self, *args, **kwargs):
        super(AddTestForm, self).__init__(*args, **kwargs)

        self.fields['test_name'].error_messages = {'required': 'Please Enter Test Name'}
        self.fields['test_category'].error_messages = {'required': 'Please Select A Test Category'}
        self.fields['description'].error_messages = {'required': 'Please Enter Description'}
        self.fields['result_type'].error_messages = {'required': 'Please Select A Result Type'}
        self.fields['percentile_score_conversion_type'].error_messages = {'required': 'Please Select A Percentile'
                                                                                      ' Score Conversion Type'}

        self.fields['test_category'].choices = []
        for test_category in TestCategory.objects.all():
            self.fields['test_category'].choices.append((test_category.pk, test_category.test_category_name))

    def add_test(self):
        test_saved = self.is_valid()
        if test_saved:
            test_name = self.cleaned_data['test_name']
            test_category = TestCategory.objects.get(pk=self.cleaned_data['test_category'])
            description = self.cleaned_data['description']
            result_type = self.cleaned_data['result_type']
            is_upward_percentile_brackets = self.cleaned_data['is_upward_percentile_brackets']
            percentile_score_conversion_type = self.cleaned_data['percentile_score_conversion_type']
            test_saved = Test.create_test(test_name=test_name, test_category=test_category, description=description,
                                          result_type=result_type,
                                          is_upward_percentile_brackets=is_upward_percentile_brackets,
                                          percentile_score_conversion_type=percentile_score_conversion_type)
        return test_saved


class AddTestsForm(forms.Form):
    add_tests_file = forms.FileField(required=True)

    def __init__(self, *args, **kwargs):
        super(AddTestsForm, self).__init__(*args, **kwargs)
        self.fields['add_tests_file'].error_messages = {'required': 'Please Choose Add Tests File'}

    def add_tests(self, request):
        if self.is_valid():
            return add_tests_from_file_upload(request.FILES['add_tests_file'])
        else:
            return False


class EditTestForm(forms.Form):
    test_pk = forms.CharField(widget=forms.HiddenInput())
    test_name = forms.CharField(max_length=200, required=True)
    test_category = forms.ChoiceField(required=True)
    description = forms.CharField(widget=forms.Textarea(), max_length=400, required=True)
    result_type = forms.ChoiceField(required=True, choices=Test.RESULT_TYPE_CHOICES)
    is_upward_percentile_brackets = forms.BooleanField(required=False)
    percentile_score_conversion_type = forms.ChoiceField(required=True,
                                                         choices=Test.PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES)

    def __init__(self, test_pk, *args, **kwargs):
        super(EditTestForm, self).__init__(*args, **kwargs)

        self.fields['test_name'].error_messages = {'required': 'Please Enter Test Name'}
        self.fields['test_category'].error_messages = {'required': 'Please Select A Test Category'}
        self.fields['description'].error_messages = {'required': 'Please Enter Description'}
        self.fields['result_type'].error_messages = {'required': 'Please Select A Result Type'}
        self.fields['percentile_score_conversion_type'].error_messages = {'required': 'Please Select A Percentile'
                                                                                      ' Score Conversion Type'}

        self.fields['test_category'].choices = []
        for test_category in TestCategory.objects.all():
            self.fields['test_category'].choices.append((test_category.pk, test_category.test_category_name))

        test = Test.objects.get(pk=test_pk)
        self.fields['test_pk'].initial = test_pk
        self.fields['test_name'].initial = test.test_name
        self.fields['test_category'].initial = test.test_category.pk
        self.fields['description'].initial = test.description
        self.fields['result_type'].initial = test.result_type
        self.fields['is_upward_percentile_brackets'].initial = test.is_upward_percentile_brackets
        self.fields['percentile_score_conversion_type'].initial = test.percentile_score_conversion_type

        self.fields['test_name'].validators = [validate_new_test_name_unique(test_pk=test_pk)]

    def edit_test(self):
        test_edited = self.is_valid()
        if test_edited:
            test_pk = self.cleaned_data['test_pk']
            test_name = self.cleaned_data['test_name']
            test_category = TestCategory.objects.get(pk=self.cleaned_data['test_category'])
            description = self.cleaned_data['description']
            result_type = self.cleaned_data['result_type']
            is_upward_percentile_brackets = self.cleaned_data['is_upward_percentile_brackets']
            percentile_score_conversion_type = self.cleaned_data['percentile_score_conversion_type']
            test_editing = Test.objects.get(pk=test_pk)
            test_edited = test_editing.edit_test_safe(test_name, test_category, description, result_type,
                                                      is_upward_percentile_brackets, percentile_score_conversion_type)
        return test_edited