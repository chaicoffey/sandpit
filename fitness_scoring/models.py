from django.db import models

# Create your models here.
#delete me...what is this crappy comment?


class School(models.Model):
    name = models.CharField(max_length=300)
    subscriptionPaid = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def get_school_name_padded(self, padding):
        return self.name+"&nbsp"*(padding - len(self.name))

    def getSubscriptionPaidText(self):
        if self.subscriptionPaid:
            return 'Paid'
        else:
            return 'Unpaid'

def get_school_name_max_length():
    return len(max([school.name for school in School.objects.all()], key=len))

class User(models.Model):
    username = models.CharField(max_length=100, primary_key=True)
    password = models.CharField(max_length=128)

    def __unicode__(self):
        return self.username


class SuperUser(models.Model):
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.user.username


class Teacher(models.Model):
    firstname = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    school_id = models.ForeignKey(School)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.firstname + " " + self.surname


class Administrator(models.Model):
    school_id = models.ForeignKey(School)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.user.username


class Student(models.Model):
    student_id = models.CharField(max_length=30)
    school_id = models.ForeignKey(School)
    firstname = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    gender = models.CharField(max_length=1)
    dob = models.DateField()

    def __unicode__(self):
        return self.firstname + " " + self.surname


def create_or_update_student(create_update, limited, student_id, school_id, firstname, surname, gender, dob):
#   create_update, if true will only create, if false can create or update
#   limited, if true  will only create if unique name and id
#                     will only update if same name and id
#            if false will create if unique id
#                     will update if same id
#   if all details the same then leave alone

    unique_student_id = (len(Student.objects.filter(school_id=school_id, student_id=student_id)) == 0)
    unique_name = (len(Student.objects.filter(school_id=school_id, firstname=firstname, surname=surname)) == 0)

    if unique_student_id and unique_name:
        mode = 'Unique'
    elif (not unique_student_id) and unique_name:
        mode = 'Duplicate ID, Unique Name'
    elif unique_student_id and not unique_name:
        mode = 'Unique ID, Duplicate Name'
    elif (not unique_student_id) and (not unique_name):
        student = Student.objects.get(school_id=school_id, student_id=student_id)
        same_details = student.gender == gender and student.dob == dob
        if same_details:
            mode = 'Duplicate'
        else:
            mode = 'Duplicate, Unique Details'

    # check update_mode is valid
    if mode == 'Unique' or (mode == 'Unique ID, Duplicate Name' and (not limited)):
        Student.objects.create(student_id=student_id, school_id=school_id, firstname=firstname, surname=surname, gender=gender, dob=dob)
    elif (not create_update) and (mode == 'Duplicate, Unique Details' or (mode == 'Duplicate ID, Unique Name' and (not limited))):
        student = Student.objects.get(school_id=school_id, student_id=student_id)
        student.firstname = firstname
        student.surname = surname
        student.gender = gender
        student.dob = dob
        student.save()

    return mode


class Class(models.Model):
    year = models.DateField()
    class_name = models.CharField(max_length=200)
    school_id = models.ForeignKey(School)

    def __unicode__(self):
        return self.class_name


class TestCategory(models.Model):
    test_category_name = models.CharField(max_length=200, primary_key=True)

    def __unicode__(self):
        return self.test_category_name


class Test(models.Model):
    RESULT_TYPE_CHOICES = (
        ('DOUBLE', 'Double'),
        ('TIME', 'Time'),
        ('INTEGER', 'Integer')
    )
    PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES = (
        ('DIRECT', 'Direct'),
        ('HIGH_MIDDLE', 'High Middle')
    )
    test_name = models.CharField(max_length=200, primary_key=True)
    test_category_name = models.ForeignKey(TestCategory)
    description = models.CharField(max_length=400)
    result_type = models.CharField(max_length=20, choices=RESULT_TYPE_CHOICES, default='DOUBLE')
    is_upward_percentile_brackets = models.BooleanField(default=True)
    percentile_score_conversion_type = models.CharField(max_length=20,
                                                        choices=PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES,
                                                        default='DIRECT')

    def __unicode__(self):
        return self.test_name


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
