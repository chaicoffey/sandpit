from django import forms
from django.contrib import messages
from fitness_scoring.models import Student, School, Class, Teacher, TestCategory, Test
from fitness_scoring.validators import validate_school_unique, validate_test_category_unique, validate_test_unique
from fitness_scoring.validators import validate_no_space
from fitness_scoring.fileio import add_schools_from_file_upload, add_test_categories_from_file_upload
from fitness_scoring.fileio import add_tests_from_file_upload
from django.core.validators import MinLengthValidator
import datetime


class AddStudentForm(forms.Form):
    student_id = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=100)
    surname = forms.CharField(max_length=100)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    dob = forms.DateField(input_formats=['%d/%m/%Y'], help_text='(dd/mm/yyyy)')

    def handle_posted_form(self, request, messages_tag):
        form_posted_from = (request.POST.get(self.get_add_student_button_name()) == self.get_add_student_button_value())
        if form_posted_from:
            if self.is_valid():
                student_string = self.get_first_name() + " " + self.get_surname() + " (" + self.get_student_id() + ")"
                if self.add_student_safe(School.objects.get(name=request.session.get('school_name', None))):
                    messages.success(request, "Student Added: " + student_string, extra_tags=messages_tag)
                else:
                    messages.success(request, "Error Adding Student: " + student_string + " (Student ID Already Exists)", extra_tags=messages_tag)
            else:
                messages.success(request, "Add Student Validation Error", extra_tags=messages_tag)
        return form_posted_from

    def add_student_safe(self, school_id):
        return Student.create_student(check_name=False, student_id=self.get_student_id(), school_id=school_id, first_name=self.get_first_name(), surname=self.get_surname(), gender=self.get_gender(), dob=self.get_dob())

    def get_student_id(self):
        return self.cleaned_data['student_id']

    def get_first_name(self):
        return self.cleaned_data['first_name']

    def get_surname(self):
        return self.cleaned_data['surname']

    def get_gender(self):
        return self.cleaned_data['gender']

    def get_dob(self):
        return self.cleaned_data['dob']

    @staticmethod
    def get_add_student_button_name():
        return "AddStudentIdentifier"

    @staticmethod
    def get_add_student_button_value():
        return "AddStudent"

    @staticmethod
    def get_form_name():
        return "addStudentForm"

    @staticmethod
    def get_error_message_label_id_prefix():
        return "addStudentErrorMessageLabel_"

    @staticmethod
    def get_javascript_validation_call():
        return "validateAddStudentFields()"

    @staticmethod
    def get_javascript_validation_function():
        return \
            "function validateAddStudentFields()\n\
            {\n\
            \n\
                function isDate(dateString)\n\
                {\n\
                    var correctFormat = (dob.length == 10) && (dob.charAt(2) == '\/') && (dob.charAt(5) == '\/')\n\
                    if(correctFormat) {\n\
                        var dayString = dob.substring(0,2);\n\
                        var monthString = dob.substring(3,5);\n\
                        var yearString = dob.substring(6,10);\n\
                        correctFormat = (/^[0-9]+$/.test(dayString)) && (/^[0-9]+$/.test(monthString)) && (/^[0-9]+$/.test(yearString));\n\
                        if(correctFormat) {\n\
                            date = new Date(yearString, monthString - 1, dayString);\n\
                            correctFormat = (date.getDate() == dayString) && ((date.getMonth() + 1) == monthString) && (date.getFullYear() == yearString)\n\
                        }\n\
                    }\n\
                    return correctFormat;\n\
                }\n\
                var form = document.forms['addStudentForm'];\n\
            \n\
                var studentIdErrorMessage = document.getElementById('addStudentErrorMessageLabel_student_id');\n\
                var firstNameErrorMessage = document.getElementById('addStudentErrorMessageLabel_first_name');\n\
                var surnameErrorMessage = document.getElementById('addStudentErrorMessageLabel_surname');\n\
                var genderErrorMessage = document.getElementById('addStudentErrorMessageLabel_gender');\n\
                var dobErrorMessage = document.getElementById('addStudentErrorMessageLabel_dob');\n\
                \n\
                studentIdErrorMessage.style.display = 'none';\n\
                firstNameErrorMessage.style.display = 'none';\n\
                surnameErrorMessage.style.display = 'none';\n\
                genderErrorMessage.style.display = 'none';\n\
                dobErrorMessage.style.display = 'none';\n\
                \n\
                var studentId = form.elements['student_id'].value;\n\
                var studentIdEntered = (studentId != '')\n\
                if(!studentIdEntered) {\n\
                    studentIdErrorMessage.style.display = 'inherit';\n\
                    studentIdErrorMessage.innerHTML = '- Please enter Student Id';\n\
                }\n\
            \n\
                var firstName = form.elements['first_name'].value;\n\
                var firstNameEntered = (firstName != '')\n\
                if(!firstNameEntered) {\n\
                    firstNameErrorMessage.style.display = 'inherit';\n\
                    firstNameErrorMessage.innerHTML = '- Please enter First Name';\n\
                }\n\
            \n\
                var surname = form.elements['surname'].value;\n\
                var surnameEntered = (surname != '')\n\
                if(!surnameEntered) {\n\
                    surnameErrorMessage.style.display = 'inherit';\n\
                    surnameErrorMessage.innerHTML = '- Please enter Surname';\n\
                }\n\
            \n\
                var gender = form.elements['gender'].value;\n\
                var genderEntered = (gender != '')\n\
                if(!genderEntered) {\n\
                    genderErrorMessage.style.display = 'inherit';\n\
                    genderErrorMessage.innerHTML = '- Please enter Gender';\n\
                }\n\
            \n\
                var dob = form.elements['dob'].value;\n\
                var dobEntered = (dob != '')\n\
                var dobCorrectFormat = isDate(dob);\n\
                var dobValid = dobEntered && dobCorrectFormat\n\
                if(!dobValid) {\n\
                    dobErrorMessage.style.display = 'inherit';\n\
                    if(!dobEntered)\n\
                        dobErrorMessage.innerHTML = '- Please enter DOB';\n\
                    else if(!dobCorrectFormat)\n\
                        dobErrorMessage.innerHTML = '- Invalid date (make sure date is in form dd/mm/yyyy)';\n\
                }\n\
            \n\
                return studentIdEntered && firstNameEntered && surnameEntered && genderEntered && dobValid;\n\
            \n\
            }\n"


class EditStudentForm(forms.Form):
    student_pk = forms.CharField(widget=forms.HiddenInput())
    student_id = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=100)
    surname = forms.CharField(max_length=100)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    dob = forms.DateField(input_formats=['%d/%m/%Y'], help_text='(dd/mm/yyyy)')

    def handle_posted_form(self, request, messages_tag):
        form_posted_from = (request.POST.get(self.get_edit_student_button_name()) == self.get_edit_student_button_value())
        if form_posted_from:
            if self.is_valid():
                student_string = self.get_first_name() + " " + self.get_surname() + " (" + self.get_student_id() + ")"
                if self.edit_student_safe(School.objects.get(name=request.session.get('school_name', None))):
                    messages.success(request, "Student Edited: " + student_string, extra_tags=messages_tag)
                else:
                    messages.success(request, "Error Editing Student: " + student_string + " (Student ID Already Exists)", extra_tags=messages_tag)
            else:
                messages.success(request, "Edit Student Validation Error", extra_tags=messages_tag)
        return form_posted_from

    def edit_student_safe(self, school_id):
        return Student.objects.get(pk=self.get_student_pk()).edit_student_safe(student_id=self.get_student_id(), school_id=school_id, first_name=self.get_first_name(), surname=self.get_surname(), gender=self.get_gender(), dob=self.get_dob())

    def get_student_pk(self):
        return self.cleaned_data['student_pk']

    def get_student_id(self):
        return self.cleaned_data['student_id']

    def get_first_name(self):
        return self.cleaned_data['first_name']

    def get_surname(self):
        return self.cleaned_data['surname']

    def get_gender(self):
        return self.cleaned_data['gender']

    def get_dob(self):
        return self.cleaned_data['dob']

    @staticmethod
    def get_edit_student_button_name():
        return "EditStudentIdentifier"

    @staticmethod
    def get_edit_student_button_value():
        return "EditStudent"

    @staticmethod
    def get_form_name():
        return "editStudentForm"

    @staticmethod
    def get_modal_id():
        return "editStudentModal"

    @staticmethod
    def get_error_message_label_id_prefix():
        return "editStudentErrorMessageLabel_"

    @staticmethod
    def get_javascript_validation_call():
        return "validateEditStudentFields()"

    @staticmethod
    def get_javascript_show_modal_call():
        return "showEditStudentModal"

    @staticmethod
    def get_javascript_validation_function():
        return \
            "function validateEditStudentFields()\n\
            {\n\
            \n\
                function isDate(dateString)\n\
                {\n\
                    var correctFormat = (dob.length == 10) && (dob.charAt(2) == '\/') && (dob.charAt(5) == '\/')\n\
                    if(correctFormat) {\n\
                        var dayString = dob.substring(0,2);\n\
                        var monthString = dob.substring(3,5);\n\
                        var yearString = dob.substring(6,10);\n\
                        correctFormat = (/^[0-9]+$/.test(dayString)) && (/^[0-9]+$/.test(monthString)) && (/^[0-9]+$/.test(yearString));\n\
                        if(correctFormat) {\n\
                            date = new Date(yearString, monthString - 1, dayString);\n\
                            correctFormat = (date.getDate() == dayString) && ((date.getMonth() + 1) == monthString) && (date.getFullYear() == yearString)\n\
                        }\n\
                    }\n\
                    return correctFormat;\n\
                }\n\
                var form = document.forms['editStudentForm'];\n\
            \n\
                var studentIdErrorMessage = document.getElementById('editStudentErrorMessageLabel_student_id');\n\
                var firstNameErrorMessage = document.getElementById('editStudentErrorMessageLabel_first_name');\n\
                var surnameErrorMessage = document.getElementById('editStudentErrorMessageLabel_surname');\n\
                var genderErrorMessage = document.getElementById('editStudentErrorMessageLabel_gender');\n\
                var dobErrorMessage = document.getElementById('editStudentErrorMessageLabel_dob');\n\
                \n\
                studentIdErrorMessage.style.display = 'none';\n\
                firstNameErrorMessage.style.display = 'none';\n\
                surnameErrorMessage.style.display = 'none';\n\
                genderErrorMessage.style.display = 'none';\n\
                dobErrorMessage.style.display = 'none';\n\
                \n\
                var studentId = form.elements['student_id'].value;\n\
                var studentIdEntered = (studentId != '')\n\
                if(!studentIdEntered) {\n\
                    studentIdErrorMessage.style.display = 'inherit';\n\
                    studentIdErrorMessage.innerHTML = '- Please enter Student Id';\n\
                }\n\
            \n\
                var firstName = form.elements['first_name'].value;\n\
                var firstNameEntered = (firstName != '')\n\
                if(!firstNameEntered) {\n\
                    firstNameErrorMessage.style.display = 'inherit';\n\
                    firstNameErrorMessage.innerHTML = '- Please enter First Name';\n\
                }\n\
            \n\
                var surname = form.elements['surname'].value;\n\
                var surnameEntered = (surname != '')\n\
                if(!surnameEntered) {\n\
                    surnameErrorMessage.style.display = 'inherit';\n\
                    surnameErrorMessage.innerHTML = '- Please enter Surname';\n\
                }\n\
            \n\
                var gender = form.elements['gender'].value;\n\
                var genderEntered = (gender != '')\n\
                if(!genderEntered) {\n\
                    genderErrorMessage.style.display = 'inherit';\n\
                    genderErrorMessage.innerHTML = '- Please enter Gender';\n\
                }\n\
            \n\
                var dob = form.elements['dob'].value;\n\
                var dobEntered = (dob != '')\n\
                var dobCorrectFormat = isDate(dob);\n\
                var dobValid = dobEntered && dobCorrectFormat\n\
                if(!dobValid) {\n\
                    dobErrorMessage.style.display = 'inherit';\n\
                    if(!dobEntered)\n\
                        dobErrorMessage.innerHTML = '- Please enter DOB';\n\
                    else if(!dobCorrectFormat)\n\
                        dobErrorMessage.innerHTML = '- Invalid date (make sure date is in form dd/mm/yyyy)';\n\
                }\n\
            \n\
                return studentIdEntered && firstNameEntered && surnameEntered && genderEntered && dobValid;\n\
            \n\
            }\n"

    @staticmethod
    def get_javascript_show_modal_function():
        return \
            "function showEditStudentModal(student_pk, student_id, first_name, surname, gender, dob)\n\
            {\n\
            \n\
                var modalForm = document.forms['editStudentForm'];\n\
            \n\
                modalForm.elements['student_pk'].value = student_pk;\n\
                modalForm.elements['student_id'].value = student_id;\n\
                modalForm.elements['first_name'].value = first_name;\n\
                modalForm.elements['surname'].value = surname;\n\
                modalForm.elements['gender'].value = gender;\n\
                modalForm.elements['dob'].value = dob;\n\
                validateEditStudentFields()\n\
            \n\
                $('#editStudentModal').modal('show');\n\
            \n\
            }\n"


class AddTeacherForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    surname = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=128)

    def handle_posted_form(self, request, messages_tag):
        form_posted_from = (request.POST.get(self.get_add_teacher_button_name()) == self.get_add_teacher_button_value())
        if form_posted_from:
            if self.is_valid():
                teacher_string = self.get_first_name() + " " + self.get_surname() + " (" + self.get_username() + ")"
                if self.add_teacher_safe(School.objects.get(name=request.session.get('school_name', None))):
                    messages.success(request, "Teacher Added: " + teacher_string, extra_tags=messages_tag)
                else:
                    messages.success(request, "Error Adding Teacher: " + teacher_string + " (Username Already Exists)", extra_tags=messages_tag)
            else:
                messages.success(request, "Add Teacher Validation Error", extra_tags=messages_tag)
        return form_posted_from

    def add_teacher_safe(self, school_id):
        return Teacher.create_teacher(check_name=False, first_name=self.get_first_name(), surname=self.get_surname(), school_id=school_id, username=self.get_username(), password=self.get_password())

    def get_first_name(self):
        return self.cleaned_data['first_name']

    def get_surname(self):
        return self.cleaned_data['surname']

    def get_username(self):
        return self.cleaned_data['username']

    def get_password(self):
        return self.cleaned_data['password']

    @staticmethod
    def get_add_teacher_button_name():
        return "AddTeacherIdentifier"

    @staticmethod
    def get_add_teacher_button_value():
        return "AddTeacher"

    @staticmethod
    def get_form_name():
        return "addTeacherForm"

    @staticmethod
    def get_error_message_label_id_prefix():
        return "addTeacherErrorMessageLabel_"

    @staticmethod
    def get_javascript_validation_call():
        return "validateAddTeacherFields()"

    @staticmethod
    def get_javascript_validation_function():
        return \
            "function validateAddTeacherFields()\n\
            {\n\
            \n\
                var form = document.forms['addTeacherForm'];\n\
            \n\
                var firstNameErrorMessage = document.getElementById('addTeacherErrorMessageLabel_first_name');\n\
                var surnameErrorMessage = document.getElementById('addTeacherErrorMessageLabel_surname');\n\
                var usernameErrorMessage = document.getElementById('addTeacherErrorMessageLabel_username');\n\
                var passwordErrorMessage = document.getElementById('addTeacherErrorMessageLabel_password');\n\
                \n\
                firstNameErrorMessage.style.display = 'none';\n\
                surnameErrorMessage.style.display = 'none';\n\
                usernameErrorMessage.style.display = 'none';\n\
                passwordErrorMessage.style.display = 'none';\n\
                \n\
                var firstName = form.elements['first_name'].value;\n\
                var firstNameEntered = (firstName != '')\n\
                if(!firstNameEntered) {\n\
                    firstNameErrorMessage.style.display = 'inherit';\n\
                    firstNameErrorMessage.innerHTML = '- Please enter First Name';\n\
                }\n\
                \n\
                var surname = form.elements['surname'].value;\n\
                var surnameEntered = (surname != '')\n\
                if(!surnameEntered) {\n\
                    surnameErrorMessage.style.display = 'inherit';\n\
                    surnameErrorMessage.innerHTML = '- Please enter Surname';\n\
                }\n\
                \n\
                var username = form.elements['username'].value;\n\
                var usernameEntered = (username != '')\n\
                if(!usernameEntered) {\n\
                    usernameErrorMessage.style.display = 'inherit';\n\
                    usernameErrorMessage.innerHTML = '- Please enter Username';\n\
                }\n\
                \n\
                var password = form.elements['password'].value;\n\
                var passwordEntered = (password != '')\n\
                if(!passwordEntered) {\n\
                    passwordErrorMessage.style.display = 'inherit';\n\
                    passwordErrorMessage.innerHTML = '- Please enter Password';\n\
                }\n\
            \n\
                return firstNameEntered && surnameEntered && usernameEntered && passwordEntered;\n\
            \n\
            }\n"


class EditTeacherForm(forms.Form):
    teacher_pk = forms.CharField(widget=forms.HiddenInput())
    first_name = forms.CharField(max_length=100)
    surname = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=128)

    def handle_posted_form(self, request, messages_tag):
        form_posted_from = (request.POST.get(self.get_edit_teacher_button_name()) == self.get_edit_teacher_button_value())
        if form_posted_from:
            if self.is_valid():
                teacher_string = self.get_first_name() + " " + self.get_surname() + " (" + self.get_username() + ")"
                if self.edit_teacher_safe(School.objects.get(name=request.session.get('school_name', None))):
                    messages.success(request, "Teacher Edited: " + teacher_string, extra_tags=messages_tag)
                else:
                    messages.success(request, "Error Editing Teacher: " + teacher_string + " (Username Already Exists)", extra_tags=messages_tag)
            else:
                messages.success(request, "Edit Teacher Validation Error", extra_tags=messages_tag)
        return form_posted_from

    def edit_teacher_safe(self, school_id):
        return Teacher.objects.get(pk=self.get_teacher_pk()).edit_teacher_safe(first_name=self.get_first_name(), surname=self.get_surname(), school_id=school_id, username=self.get_username(), password=self.get_password())

    def get_teacher_pk(self):
        return self.cleaned_data['teacher_pk']

    def get_first_name(self):
        return self.cleaned_data['first_name']

    def get_surname(self):
        return self.cleaned_data['surname']

    def get_username(self):
        return self.cleaned_data['username']

    def get_password(self):
        return self.cleaned_data['password']

    @staticmethod
    def get_edit_teacher_button_name():
        return "EditTeacherIdentifier"

    @staticmethod
    def get_edit_teacher_button_value():
        return "EditTeacher"

    @staticmethod
    def get_form_name():
        return "editTeacherForm"

    @staticmethod
    def get_modal_id():
        return "editTeacherModal"

    @staticmethod
    def get_error_message_label_id_prefix():
        return "editTeacherErrorMessageLabel_"

    @staticmethod
    def get_javascript_validation_call():
        return "validateEditTeacherFields()"

    @staticmethod
    def get_javascript_show_modal_call():
        return "showEditTeacherModal"

    @staticmethod
    def get_javascript_validation_function():
        return \
            "function validateEditTeacherFields()\n\
            {\n\
            \n\
                var form = document.forms['editTeacherForm'];\n\
            \n\
                var firstNameErrorMessage = document.getElementById('editTeacherErrorMessageLabel_first_name');\n\
                var surnameErrorMessage = document.getElementById('editTeacherErrorMessageLabel_surname');\n\
                var usernameErrorMessage = document.getElementById('editTeacherErrorMessageLabel_username');\n\
                var passwordErrorMessage = document.getElementById('editTeacherErrorMessageLabel_password');\n\
                \n\
                firstNameErrorMessage.style.display = 'none';\n\
                surnameErrorMessage.style.display = 'none';\n\
                usernameErrorMessage.style.display = 'none';\n\
                passwordErrorMessage.style.display = 'none';\n\
                \n\
                var firstName = form.elements['first_name'].value;\n\
                var firstNameEntered = (firstName != '')\n\
                if(!firstNameEntered) {\n\
                    firstNameErrorMessage.style.display = 'inherit';\n\
                    firstNameErrorMessage.innerHTML = '- Please enter First Name';\n\
                }\n\
                \n\
                var surname = form.elements['surname'].value;\n\
                var surnameEntered = (surname != '')\n\
                if(!surnameEntered) {\n\
                    surnameErrorMessage.style.display = 'inherit';\n\
                    surnameErrorMessage.innerHTML = '- Please enter Surname';\n\
                }\n\
                \n\
                var username = form.elements['username'].value;\n\
                var usernameEntered = (username != '')\n\
                if(!usernameEntered) {\n\
                    usernameErrorMessage.style.display = 'inherit';\n\
                    usernameErrorMessage.innerHTML = '- Please enter Username';\n\
                }\n\
                \n\
                var password = form.elements['password'].value;\n\
                var passwordEntered = (password != '')\n\
                if(!passwordEntered) {\n\
                    passwordErrorMessage.style.display = 'inherit';\n\
                    passwordErrorMessage.innerHTML = '- Please enter Password';\n\
                }\n\
            \n\
                return firstNameEntered && surnameEntered && usernameEntered && passwordEntered;\n\
            \n\
            }\n"

    @staticmethod
    def get_javascript_show_modal_function():
        return \
            "function showEditTeacherModal(teacher_pk, first_name, surname, username, password)\n\
            {\n\
            \n\
                var modalForm = document.forms['editTeacherForm'];\n\
            \n\
                modalForm.elements['teacher_pk'].value = teacher_pk;\n\
                modalForm.elements['first_name'].value = first_name;\n\
                modalForm.elements['surname'].value = surname;\n\
                modalForm.elements['username'].value = username;\n\
                modalForm.elements['password'].value = password;\n\
                validateEditTeacherFields()\n\
            \n\
                $('#editTeacherModal').modal('show');\n\
            \n\
            }\n"


class AddClassForm(forms.Form):
    year = forms.ChoiceField()
    class_name = forms.CharField(max_length=200)
    teacher = forms.ChoiceField(required=False)

    def __init__(self, school_id, *args, **kwargs):
        super(AddClassForm, self).__init__(*args, **kwargs)
        current_year = datetime.datetime.now().year
        YEAR_CHOICES = []
        for year in range(2000, (current_year+2)):
            YEAR_CHOICES.append((str(year), str(year)))
        self.fields['year'].choices = YEAR_CHOICES
        self.fields['year'].initial = str(current_year)
        TEACHER_CHOICES = [('', '')]
        for teacher in Teacher.objects.filter(school_id=school_id):
            TEACHER_CHOICES.append((teacher.pk, teacher.first_name + " " + teacher.surname + " (" + teacher.user.username + ")"))
        self.fields['teacher'].choices = TEACHER_CHOICES
        self.fields['teacher'].initial = ''

    def handle_posted_form(self, request, messages_tag):
        form_posted_from = (request.POST.get(self.get_add_class_button_name()) == self.get_add_class_button_value())
        if form_posted_from:
            if self.is_valid():
                class_string = self.get_class_name() + " (" + self.get_year() + ")"
                if self.add_class_safe(School.objects.get(name=request.session.get('school_name', None))):
                    messages.success(request, "Class Added: " + class_string, extra_tags=messages_tag)
                else:
                    messages.success(request, "Error Adding Class: " + class_string + " Already Exists", extra_tags=messages_tag)
            else:
                messages.success(request, "Add Class Validation Error", extra_tags=messages_tag)
        return form_posted_from

    def add_class_safe(self, school_id):
        return Class.create_class(year=self.get_year(), class_name=self.get_class_name(), school_id=school_id, teacher_id=self.get_teacher())

    def get_year(self):
        return self.cleaned_data['year']

    def get_class_name(self):
        return self.cleaned_data['class_name']

    def get_teacher(self):
        teacher_pk = self.cleaned_data['teacher']
        return None if (teacher_pk == '') else Teacher.objects.get(pk=teacher_pk)

    @staticmethod
    def get_add_class_button_name():
        return "AddClassIdentifier"

    @staticmethod
    def get_add_class_button_value():
        return "AddClass"

    @staticmethod
    def get_form_name():
        return "addClassForm"

    @staticmethod
    def get_error_message_label_id_prefix():
        return "addClassErrorMessageLabel_"

    @staticmethod
    def get_javascript_validation_call():
        return "validateAddClassFields()"

    @staticmethod
    def get_javascript_validation_function():
        return \
            "function validateAddClassFields()\n\
            {\n\
                \n\
                var form = document.forms['addClassForm'];\n\
                \n\
                var yearErrorMessage = document.getElementById('addClassErrorMessageLabel_year');\n\
                var classNameErrorMessage = document.getElementById('addClassErrorMessageLabel_class_name');\n\
                var teacherErrorMessage = document.getElementById('addClassErrorMessageLabel_teacher');\n\
                \n\
                yearErrorMessage.style.display = 'none';\n\
                classNameErrorMessage.style.display = 'none';\n\
                teacherErrorMessage.style.display = 'none';\n\
                \n\
                var yearSelect = form.elements['year']\n\
                var year =  yearSelect.options[yearSelect.selectedIndex].value;\n\
                var yearEntered = (year != '')\n\
                if(!yearEntered) {\n\
                    yearErrorMessage.style.display = 'inherit';\n\
                    yearErrorMessage.innerHTML = '- Please enter Year';\n\
                }\n\
                \n\
                var className = form.elements['class_name'].value;\n\
                var classNameEntered = (className != '')\n\
                if(!classNameEntered) {\n\
                    classNameErrorMessage.style.display = 'inherit';\n\
                    classNameErrorMessage.innerHTML = '- Please enter Class Name';\n\
                }\n\
                \n\
                return yearEntered && classNameEntered;\n\
                \n\
            }\n"


class EditClassForm(forms.Form):
    class_pk = forms.CharField(widget=forms.HiddenInput())
    year = forms.ChoiceField()
    class_name = forms.CharField(max_length=200)
    teacher = forms.ChoiceField(required=False)

    def __init__(self, school_id, *args, **kwargs):
        super(EditClassForm, self).__init__(*args, **kwargs)
        current_year = datetime.datetime.now().year
        YEAR_CHOICES = []
        for year in range(2000, (current_year+2)):
            YEAR_CHOICES.append((str(year), str(year)))
        self.fields['year'].choices = YEAR_CHOICES
        self.fields['year'].initial = str(current_year)
        TEACHER_CHOICES = [('', '')]
        for teacher in Teacher.objects.filter(school_id=school_id):
            TEACHER_CHOICES.append((teacher.pk, teacher.first_name + " " + teacher.surname + " (" + teacher.user.username + ")"))
        self.fields['teacher'].choices = TEACHER_CHOICES
        self.fields['teacher'].initial = ''

    def handle_posted_form(self, request, messages_tag):
        form_posted_from = (request.POST.get(self.get_edit_class_button_name()) == self.get_edit_class_button_value())
        if form_posted_from:
            if self.is_valid():
                class_string = self.get_class_name() + " (" + self.get_year() + ")"
                if self.edit_class_safe(School.objects.get(name=request.session.get('school_name', None))):
                    messages.success(request, "Class Edited: " + class_string, extra_tags=messages_tag)
                else:
                    messages.success(request, "Error Editing Class: " + class_string + " Already Exists", extra_tags=messages_tag)
            else:
                messages.success(request, "Edit Class Validation Error", extra_tags=messages_tag)
        return form_posted_from

    def edit_class_safe(self, school_id):
        return Class.objects.get(pk=self.get_class_pk()).edit_class_safe(year=self.get_year(), class_name=self.get_class_name(), school_id=school_id, teacher_id=self.get_teacher())

    def get_class_pk(self):
        return self.cleaned_data['class_pk']

    def get_year(self):
        return self.cleaned_data['year']

    def get_class_name(self):
        return self.cleaned_data['class_name']

    def get_teacher(self):
        teacher_pk = self.cleaned_data['teacher']
        return None if (teacher_pk == '') else Teacher.objects.get(pk=teacher_pk)

    @staticmethod
    def get_edit_class_button_name():
        return "EditClassIdentifier"

    @staticmethod
    def get_edit_class_button_value():
        return "EditClass"

    @staticmethod
    def get_form_name():
        return "editClassForm"

    @staticmethod
    def get_modal_id():
        return "editClassModal"

    @staticmethod
    def get_error_message_label_id_prefix():
        return "editClassErrorMessageLabel_"

    @staticmethod
    def get_javascript_validation_call():
        return "validateEditClassFields()"

    @staticmethod
    def get_javascript_show_modal_call():
        return "showEditClassModal"

    @staticmethod
    def get_javascript_validation_function():
        return \
            "function validateEditClassFields()\n\
            {\n\
                \n\
                var form = document.forms['editClassForm'];\n\
                \n\
                var yearErrorMessage = document.getElementById('editClassErrorMessageLabel_year');\n\
                var classNameErrorMessage = document.getElementById('editClassErrorMessageLabel_class_name');\n\
                var teacherErrorMessage = document.getElementById('editClassErrorMessageLabel_teacher');\n\
                \n\
                yearErrorMessage.style.display = 'none';\n\
                classNameErrorMessage.style.display = 'none';\n\
                teacherErrorMessage.style.display = 'none';\n\
                \n\
                var yearSelect = form.elements['year']\n\
                var year =  yearSelect.options[yearSelect.selectedIndex].value;\n\
                var yearEntered = (year != '')\n\
                if(!yearEntered) {\n\
                    yearErrorMessage.style.display = 'inherit';\n\
                    yearErrorMessage.innerHTML = '- Please enter Year';\n\
                }\n\
                \n\
                var className = form.elements['class_name'].value;\n\
                var classNameEntered = (className != '')\n\
                if(!classNameEntered) {\n\
                    classNameErrorMessage.style.display = 'inherit';\n\
                    classNameErrorMessage.innerHTML = '- Please enter Class Name';\n\
                }\n\
                \n\
                return yearEntered && classNameEntered;\n\
                \n\
            }\n"

    @staticmethod
    def get_javascript_show_modal_function():
        return \
            "function showEditClassModal(class_pk, year, class_name, teacher_pk)\n\
            {\n\
            \n\
                var modalForm = document.forms['editClassForm'];\n\
            \n\
                modalForm.elements['class_pk'].value = class_pk;\n\
                modalForm.elements['year'].value = year;\n\
                modalForm.elements['class_name'].value = class_name;\n\
                modalForm.elements['teacher'].value = teacher_pk;\n\
                validateEditClassFields()\n\
            \n\
                $('#editClassModal').modal('show');\n\
            \n\
            }\n"


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

    def __init__(self, school_pk=None, *args, **kwargs):
        super(EditSchoolForm, self).__init__(*args, **kwargs)
        self.fields['name'].error_messages = {'required': 'Please Enter School Name',
                                              'min_length': 'School Name Must be at Least 3 Characters',
                                              'no_space': 'School Name Must not Have Spaces in First 3 Characters'}
        if school_pk:
            school = School.objects.get(pk=school_pk)
            self.fields['school_pk'].initial = school_pk
            self.fields['name'].initial = school.name
            self.fields['subscription_paid'].initial = school.subscription_paid

    def clean(self):
        cleaned_data = super(EditSchoolForm, self).clean()
        school_pk = cleaned_data.get("school_pk")
        name = cleaned_data.get("name")

        if school_pk and name:
            school = School.objects.get(pk=school_pk)
            if (school.name != name) and School.objects.filter(name=name).exists():
                self._errors["name"] = self.error_class(['School Name Already Exists: ' + name])
                del cleaned_data["school_pk"]
                del cleaned_data["name"]
                del cleaned_data["subscription_paid"]

        return cleaned_data

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

    def __init__(self, test_category_pk=None, *args, **kwargs):
        super(EditTestCategoryForm, self).__init__(*args, **kwargs)
        self.fields['test_category_name'].error_messages = {'required': 'Please Enter Test Category Name'}
        if test_category_pk:
            test_category = TestCategory.objects.get(pk=test_category_pk)
            self.fields['test_category_pk'].initial = test_category_pk
            self.fields['test_category_name'].initial = test_category.test_category_name

    def clean(self):
        cleaned_data = super(EditTestCategoryForm, self).clean()
        test_category_pk = cleaned_data.get("test_category_pk")
        test_category_name = cleaned_data.get("test_category_name")

        if test_category_pk and test_category_name:
            test_category = TestCategory.objects.get(pk=test_category_pk)
            if (test_category.test_category_name != test_category_name) and TestCategory.objects.filter(test_category_name=test_category_name).exists():
                self._errors["test_category_name"] = self.error_class(['Test Category Name Already Exists: ' + test_category_name])
                del cleaned_data["test_category_pk"]
                del cleaned_data["test_category_name"]

        return cleaned_data

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
    description = forms.CharField(max_length=400, required=True)
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
                                          result_type=result_type, is_upward_percentile_brackets=is_upward_percentile_brackets,
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
    description = forms.CharField(max_length=400, required=True)
    result_type = forms.ChoiceField(required=True, choices=Test.RESULT_TYPE_CHOICES)
    is_upward_percentile_brackets = forms.BooleanField(required=False)
    percentile_score_conversion_type = forms.ChoiceField(required=True,
                                                         choices=Test.PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES)

    def __init__(self, test_pk=None, *args, **kwargs):
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

        if test_pk:
            test = Test.objects.get(pk=test_pk)
            self.fields['test_pk'].initial = test_pk
            self.fields['test_name'].initial = test.test_name
            self.fields['test_category'].initial = test.test_category.pk
            self.fields['description'].initial = test.description
            self.fields['result_type'].initial = test.result_type
            self.fields['is_upward_percentile_brackets'].initial = test.is_upward_percentile_brackets
            self.fields['percentile_score_conversion_type'].initial = test.percentile_score_conversion_type

    def clean(self):
        cleaned_data = super(EditTestForm, self).clean()
        test_pk = cleaned_data.get("test_pk")
        test_name = cleaned_data.get("test_name")

        if test_pk and test_name:
            test = Test.objects.get(pk=test_pk)
            if (test.test_name != test_name) and Test.objects.filter(test_name=test_name).exists():
                self._errors["test_name"] = self.error_class(['Test Name Already Exists: ' + test_name])
                del cleaned_data["test_pk"]
                del cleaned_data["test_name"]
                del cleaned_data["test_category"]
                del cleaned_data["description"]
                del cleaned_data["result_type"]
                del cleaned_data["is_upward_percentile_brackets"]
                del cleaned_data["percentile_score_conversion_type"]

        return cleaned_data

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

