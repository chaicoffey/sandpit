from django.db import models

# Create your models here.

class School(models.Model):
    name = models.CharField(max_length=300)

class User(models.Model):
    username = models.CharField(max_length=100, primary_key=True)
    password = models.CharField(max_length=128)

    def __unicode__(self):
        return self.username

class SuperUser(models.Model):
    user = models.ForeignKey(User)

class Teacher(models.Model):
    firstname = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    school_id = models.ForeignKey(School)
    user = models.ForeignKey(User)

class Administrator(models.Model):
    school_id = models.ForeignKey(School)
    user = models.ForeignKey(User)

class Student(models.Model):
    student_id = models.CharField(max_length=30, primary_key=True)
    school_id = models.ForeignKey(School)
    firstname = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    gender = models.CharField(max_length=1)
    dob = models.DateField()

class Class(models.Model):
    year = models.DateField()
    class_name = models.CharField(max_length=200)
    school_id = models.ForeignKey(School)

class TestCategory(models.Model):
    test_category_name = models.CharField(max_length=200, primary_key=True)

class Test(models.Model):
    RESULT_TYPE_CHOICES = (
        ('DOUBLE', 'Double'),
        ('TIME', 'Time'),
        ('INTEGER', 'Integer')
    )
    PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES = (
        ('DIRECT','Direct'),
        ('HIGH_MIDDLE','High Middle')
    )
    test_name = models.CharField(max_length=200, primary_key=True)
    test_category_name = models.ForeignKey(TestCategory)
    description = models.CharField(max_length=400)
    result_type = models.CharField(max_length=20, choices=RESULT_TYPE_CHOICES, default='DOUBLE')
    is_upward_percentile_brackets = models.BooleanField(default=True)
    percentile_score_conversion_type = models.CharField(max_length=20, choices=PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES, default='DIRECT')

class TeacherClassAllocation(models.Model):
    teacher_id = models.ForeignKey(Teacher)
    class_id = models.ForeignKey(Class)

class StudentClassEnrolment(models.Model):
    class_id = models.ForeignKey(Class)
    student_id = models.ForeignKey(Student)
    
class ClassTestSet(models.Model):
    class_id = models.ForeignKey(Class)
    test_name = models.ForeignKey(Test)

class StudentClassTestResult(models.Model):
    student_class_id = models.ForeignKey(StudentClassEnrolment)
    test_name = models.ForeignKey(Test)
    test_result = models.IntegerField()
    age_at_time_of_test = models.IntegerField()
    percentile = models.IntegerField()

class PercentileBracket(models.Model):
    test_name = models.ForeignKey(Test)
    percentile = models.PositiveIntegerField()
    cutoff_result = models.FloatField()
