from django import forms
from fitness_scoring.models import Student, School
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


class AddSchoolForm(forms.Form):
    name = forms.CharField(max_length=300)
    subscription_paid = forms.BooleanField(initial=False, required=False)

    def add_school_safe(self):
        return create_school_and_administrator(name=self.get_name(), subscription_paid=self.get_subscription_paid())

    def get_name(self):
        return self.cleaned_data['name']

    def get_subscription_paid(self):
        return self.cleaned_data['subscription_paid']


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