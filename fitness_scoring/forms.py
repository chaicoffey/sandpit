from django import forms
from fitness_scoring.models import Student


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