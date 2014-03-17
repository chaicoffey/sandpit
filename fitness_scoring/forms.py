from django import forms
from fitness_scoring.models import Student, Class, TeacherClassAllocation, Teacher


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


#class EditTeacherClassAllocationForm(forms.ModelForm):
#    class Meta:
#        model = TeacherClassAllocation