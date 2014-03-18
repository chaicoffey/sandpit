from django.db import models
import datetime

# Create your models here.


def create_school_and_administrator(name, subscription_paid):

    school_created = create_school(name, subscription_paid)

    if school_created:

        school = School.objects.get(name=name)

        username_base = 'admin_' + name[0:3]
        if not create_administrator(username=username_base, password='admin', school_id=school):
            incremental = 1
            while not create_administrator(username=(username_base + str(incremental)), password='admin', school_id=school):
                incremental += 1

    return school_created


class School(models.Model):
    name = models.CharField(max_length=300, unique=True)
    subscription_paid = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def get_school_name_padded(self, padding):
        return self.name+"&nbsp"*(padding - len(self.name))

    def get_subscription_paid_text(self):
        if self.subscription_paid:
            return 'Paid'
        else:
            return 'Unpaid'

    def delete_school_safe(self):
        school_not_used = (len(Teacher.objects.filter(school_id=self)) == 0) and (len(Class.objects.filter(school_id=self)) == 0) and (len(Student.objects.filter(school_id=self)) == 0)
        if school_not_used:
            administrator_to_delete = Administrator.objects.get(school_id=self)
            administrator_to_delete.user.delete()
            administrator_to_delete.delete()
            self.delete()
        return school_not_used

    def edit_school_safe(self, name, subscription_paid):
        is_edit_safe = (self.name == name) or (len(School.objects.filter(name=name)) == 0)
        if is_edit_safe:
            self.name = name
            self.subscription_paid = subscription_paid
            self.save()
        return is_edit_safe


def create_school(name, subscription_paid):

    school_name_unique = (len(School.objects.filter(name=name)) == 0)

    if school_name_unique:
        School.objects.create(name=name, subscription_paid=subscription_paid)

    return school_name_unique


def update_school(name, subscription_paid):

    school_updated = False

    school_name_exists = (len(School.objects.filter(name=name)) == 1)
    if school_name_exists:
        school = School.objects.get(name=name)
        school_updated = not (school.subscription_paid == subscription_paid)
        if school_updated:
            school.subscription_paid = subscription_paid
            school.save()

    return school_updated


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
    first_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    school_id = models.ForeignKey(School)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.first_name + " " + self.surname


def create_teacher(check_name, first_name, surname, school_id, username, password):

    username_unique = (len(User.objects.filter(username=username)) == 0)
    if check_name:
        username_unique = username_unique and (len(Teacher.objects.filter(school_id=school_id, first_name=first_name, surname=surname)) == 0)

    if username_unique:
        user = User.objects.create(username=username, password=password)
        Teacher.objects.create(first_name=first_name, surname=surname, school_id=school_id, user=user)

    return username_unique


def update_teacher(check_name, first_name, surname, school_id, username, password):

    user_exists = (len(User.objects.filter(username=username)) == 1)

    teacher_exists = False
    if user_exists:
        user = User.objects.get(username=username)
        if check_name:
            teacher_exists = (len(Teacher.objects.filter(school_id=school_id, first_name=first_name, surname=surname, user=user)) == 1)
        else:
            teacher_exists = (len(Teacher.objects.filter(school_id=school_id, user=user)) == 1)

    teacher_updated = False
    if teacher_exists:
        teacher = Teacher.objects.get(user=user)
        teacher_updated = not ((teacher.first_name == first_name) and (teacher.surname == surname) and (teacher.school_id == school_id) and (user.password == password))

    if teacher_updated:
        teacher.first_name = first_name
        teacher.surname = surname
        teacher.school_id = school_id
        teacher.save()
        user.password = password
        user.save()

    return teacher_updated


class Administrator(models.Model):
    school_id = models.ForeignKey(School)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.user.username


def create_administrator(username, password, school_id):

    username_unique = (len(User.objects.filter(username=username)) == 0)

    if username_unique:
        user = User.objects.create(username=username, password=password)
        Administrator.objects.create(school_id=school_id, user=user)

    return username_unique


class Student(models.Model):
    student_id = models.CharField(max_length=30)
    school_id = models.ForeignKey(School)
    first_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    gender = models.CharField(max_length=1)
    dob = models.DateField()

    def __unicode__(self):
        return self.first_name + " " + self.surname


def create_student(check_name, student_id, school_id, first_name, surname, gender, dob):

    student_unique = (len(Student.objects.filter(school_id=school_id, student_id=student_id)) == 0)
    if check_name:
        student_unique = student_unique and (len(Student.objects.filter(school_id=school_id,
                                                                        first_name=first_name,
                                                                        surname=surname)) == 0)

    if student_unique:
        Student.objects.create(student_id=student_id, school_id=school_id, first_name=first_name, surname=surname, gender=gender, dob=dob)

    return student_unique


def update_student(check_name, student_id, school_id, first_name, surname, gender, dob):

    if check_name:
        student_exists = (len(Student.objects.filter(school_id=school_id, student_id=student_id, first_name=first_name, surname=surname)) == 1)
    else:
        student_exists = (len(Student.objects.filter(school_id=school_id, student_id=student_id)) == 1)

    student_updated = student_exists
    if student_exists:
        student = Student.objects.get(school_id=school_id, student_id=student_id)
        student_updated = not ((student.school_id == school_id) and (student.first_name == first_name) and (student.surname == surname) and (student.gender == gender) and (student.dob == datetime.datetime.strptime(dob, "%Y-%m-%d").date()))
        if student_updated:
            student.school_id = school_id
            student.first_name = first_name
            student.surname = surname
            student.gender = gender
            student.dob = dob
            student.save()

    return student_updated


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
