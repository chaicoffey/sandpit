from django import forms
from fitness_scoring.models import Student, School, Class, TeacherClassAllocation, Teacher
from fitness_scoring.models import create_school_and_administrator


class AddStudentForm(forms.Form):
    student_id = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=100)
    surname = forms.CharField(max_length=100)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    dob = forms.DateField(input_formats=['%d/%m/%Y'], help_text='(dd/mm/yyyy)')


class AddStudentsForm(forms.Form):
    add_students_file = forms.FileField()


class EditStudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ('school_id',)


class AddTeacherForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    surname = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=128)


class AddTeachersForm(forms.Form):
    add_teachers_file = forms.FileField()


class EditTeacherForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    surname = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=128)


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

    def add_school_safe(self):
        return create_school_and_administrator(name=self.get_name(), subscription_paid=self.get_subscription_paid())

    def get_name(self):
        return self.cleaned_data['name']

    def get_subscription_paid(self):
        return self.cleaned_data['subscription_paid']

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
                var schoolName = form.elements['name'].value\n\
                var schoolNameEntered = (schoolName != '')\n\
                var schoolNameLettersValid = (schoolName.length >= 3) && (/^[a-zA-Z][a-zA-Z][a-zA-Z]/i.test(schoolName))\n\
                var schoolNameValid = schoolNameEntered && schoolNameLettersValid\n\
                if(!schoolNameValid) {\n\
                    var schoolNameErrorMessage = document.getElementById('addSchoolErrorMessageLabel_name')\n\
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
                var schoolName = form.elements['name'].value\n\
                var schoolNameEntered = (schoolName != '')\n\
                var schoolNameLettersValid = (schoolName.length >= 3) && (/^[a-zA-Z][a-zA-Z][a-zA-Z]/i.test(schoolName))\n\
                var schoolNameValid = schoolNameEntered && schoolNameLettersValid\n\
                if(!schoolNameValid) {\n\
                    var schoolNameErrorMessage = document.getElementById('editSchoolErrorMessageLabel_name')\n\
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
            \n\
                $('#editSchoolModal').modal('show');\n\
            \n\
            }\n"