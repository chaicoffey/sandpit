from django import forms
from django.contrib import messages
from fitness_scoring.models import Student, School, Class, Teacher


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


class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        exclude = ('school_id',)

    def __init__(self, *args, **kwargs):
        self.school_id = None
        if 'school_id' in kwargs:
            # First pop your kwargs that may bother the parent __init__ method
            self.school_id = kwargs.pop('school_id')
        # Then, let the ModelForm initialize:
        super(ClassForm, self).__init__(*args, **kwargs)
        if self.school_id is not None:
            # Finally, access the fields dict that was created by the super().__init__ call
            self.fields['teachers'].queryset = Teacher.objects.filter(school_id=self.school_id)


class AddClassForm(ClassForm):
    pass


class EditClassForm(ClassForm):
    pass


class AddSchoolForm(forms.Form):
    name = forms.CharField(max_length=300)
    subscription_paid = forms.BooleanField(initial=False, required=False)

    def handle_posted_form(self, request, messages_tag):
        form_posted_from = (request.POST.get(self.get_add_school_button_name()) == self.get_add_school_button_value())
        if form_posted_from:
            if self.is_valid():
                if self.add_school_safe():
                    messages.success(request, "School Added: " + self.get_name(), extra_tags=messages_tag)
                else:
                    messages.success(request, "Error Adding School: " + self.get_name() + " (School Name Already Exists)", extra_tags=messages_tag)
            else:
                messages.success(request, "Add School Validation Error", extra_tags=messages_tag)
        return form_posted_from

    def add_school_safe(self):
        return School.create_school_and_administrator(name=self.get_name(), subscription_paid=self.get_subscription_paid())

    def get_name(self):
        return self.cleaned_data['name']

    def get_subscription_paid(self):
        return self.cleaned_data['subscription_paid']

    @staticmethod
    def get_add_school_button_name():
        return "AddSchoolIdentifier"

    @staticmethod
    def get_add_school_button_value():
        return "AddSchool"

    @staticmethod
    def get_form_name():
        return "addSchoolForm"

    @staticmethod
    def get_error_message_label_id_prefix():
        return "addSchoolErrorMessageLabel_"

    @staticmethod
    def get_javascript_validation_call():
        return "validateAddSchoolFields()"

    @staticmethod
    def get_javascript_validation_function():
        return \
            "function validateAddSchoolFields()\n\
            {\n\
            \n\
                var form = document.forms['addSchoolForm'];\n\
                \n\
                var schoolNameErrorMessage = document.getElementById('addSchoolErrorMessageLabel_name');\n\
                var subscriptionPaidErrorMessage = document.getElementById('addSchoolErrorMessageLabel_subscription_paid');\n\
                \n\
                schoolNameErrorMessage.style.display = 'none'\n\
                subscriptionPaidErrorMessage.style.display = 'none'\n\
                \n\
                var schoolName = form.elements['name'].value\n\
                var schoolNameEntered = (schoolName != '')\n\
                var schoolNameLettersValid = (schoolName.length >= 3) && (/^[a-zA-Z][a-zA-Z][a-zA-Z]/i.test(schoolName))\n\
                var schoolNameValid = schoolNameEntered && schoolNameLettersValid\n\
                if(!schoolNameValid) {\n\
                    schoolNameErrorMessage.style.display = 'inherit'\n\
                    if(!schoolNameEntered)\n\
                        schoolNameErrorMessage.innerHTML = '- Please enter School Name';\n\
                    else if(!schoolNameLettersValid)\n\
                        schoolNameErrorMessage.innerHTML = '- Invalid School Name (first 3 characters must be alphabetic)';\n\
                }\n\
            \n\
                var schoolSubscriptionPaid = form.elements['subscription_paid'].value\n\
                var subscriptionPaidNameValid = true\n\
            \n\
                return schoolNameValid && subscriptionPaidNameValid;\n\
            \n\
            }\n"


class EditSchoolForm(forms.Form):
    school_pk = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=300)
    subscription_paid = forms.BooleanField(initial=False, required=False)

    def handle_posted_form(self, request, messages_tag):
        form_posted_from = (request.POST.get(self.get_edit_school_button_name()) == self.get_edit_school_button_value())
        if form_posted_from:
            if self.is_valid():
                school_name_old = School.objects.get(pk=self.get_school_pk()).name
                if self.save_school():
                    messages.success(request, "School Edited: " + school_name_old, extra_tags=messages_tag)
                else:
                    messages.success(request, "Error Editing School: " + school_name_old + " (School Name Already Exists: " + self.get_name() + ")", extra_tags=messages_tag)
            else:
                messages.success(request, "Edit School Validation Error", extra_tags=messages_tag)
        return form_posted_from

    def save_school(self):
        school = School.objects.get(pk=self.get_school_pk())
        return school.edit_school_safe(self.get_name(), self.get_subscription_paid())

    def get_school_pk(self):
        return self.cleaned_data['school_pk']

    def get_name(self):
        return self.cleaned_data['name']

    def get_subscription_paid(self):
        return self.cleaned_data['subscription_paid']

    @staticmethod
    def get_edit_school_button_name():
        return "SaveSchoolIdentifier"

    @staticmethod
    def get_edit_school_button_value():
        return "SaveSchool"

    @staticmethod
    def get_form_name():
        return "editSchoolForm"

    @staticmethod
    def get_modal_id():
        return "editSchoolModal"

    @staticmethod
    def get_error_message_label_id_prefix():
        return "editSchoolErrorMessageLabel_"

    @staticmethod
    def get_javascript_validation_call():
        return "validateEditSchoolFields()"

    @staticmethod
    def get_javascript_show_modal_call():
        return "showEditSchoolModal"

    @staticmethod
    def get_javascript_validation_function():
        return \
            "function validateEditSchoolFields()\n\
            {\n\
            \n\
                var form = document.forms['editSchoolForm'];\n\
                \n\
                var schoolNameErrorMessage = document.getElementById('editSchoolErrorMessageLabel_name');\n\
                var subscriptionPaidErrorMessage = document.getElementById('editSchoolErrorMessageLabel_subscription_paid');\n\
                \n\
                schoolNameErrorMessage.style.display = 'none'\n\
                subscriptionPaidErrorMessage.style.display = 'none'\n\
                \n\
                var schoolName = form.elements['name'].value\n\
                var schoolNameEntered = (schoolName != '')\n\
                var schoolNameLettersValid = (schoolName.length >= 3) && (/^[a-zA-Z][a-zA-Z][a-zA-Z]/i.test(schoolName))\n\
                var schoolNameValid = schoolNameEntered && schoolNameLettersValid\n\
                if(!schoolNameValid) {\n\
                    schoolNameErrorMessage.style.display = 'inherit'\n\
                    if(!schoolNameEntered)\n\
                        schoolNameErrorMessage.innerHTML = '- Please enter School Name';\n\
                    else if(!schoolNameLettersValid)\n\
                        schoolNameErrorMessage.innerHTML = '- Invalid School Name (first 3 characters must be alphabetic)';\n\
                }\n\
            \n\
                var schoolSubscriptionPaid = form.elements['subscription_paid'].value\n\
                var subscriptionPaidNameValid = true\n\
            \n\
                return schoolNameValid && subscriptionPaidNameValid;\n\
            \n\
            }\n"

    @staticmethod
    def get_javascript_show_modal_function():
        return \
            "function showEditSchoolModal(school_pk, name, subscription_paid)\n\
            {\n\
            \n\
                var modalForm = document.forms['editSchoolForm']\n\
            \n\
                modalForm.elements['school_pk'].value = school_pk\n\
                modalForm.elements['name'].value = name\n\
                modalForm.elements['subscription_paid'].checked = (subscription_paid == 'True');\n\
                validateEditSchoolFields();\n\
            \n\
                $('#editSchoolModal').modal('show');\n\
            \n\
            }\n"