from django import forms

class AddStudentForm(forms.Form):
    student_id = forms.CharField(max_length=30)
    #school_id = forms.ForeignKey(School)
    firstname = forms.CharField(max_length=100)
    surname = forms.CharField(max_length=100)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    dob = forms.DateField()
    #subject = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    #message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))
    #sender = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    #cc_myself = forms.BooleanField(required=False)
