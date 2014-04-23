from django.db import models
import datetime


class School(models.Model):
    name = models.CharField(max_length=300, unique=True)
    subscription_paid = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def get_display_items(self):
        return [self.name,
                'Paid' if self.subscription_paid else 'Unpaid',
                Administrator.objects.get(school_id=self).user.username]

    def delete_school_safe(self):
        school_not_used = (len(Teacher.objects.filter(school_id=self)) == 0) and\
                          (len(Class.objects.filter(school_id=self)) == 0) and\
                          (len(Student.objects.filter(school_id=self)) == 0)
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

    @staticmethod
    def get_display_list_headings():
        return ['School Name', 'Subscription', 'Administrator Username']

    @staticmethod
    def create_school_and_administrator(name, subscription_paid):
        school = School.create_school(name, subscription_paid) if len(name) >= 3 else None
        if school:
            Administrator.create_administrator(base_username=('admin_' + name[0:3]), school_id=school)
        return school

    @staticmethod
    def create_school(name, subscription_paid):

        if not School.objects.filter(name=name).exists():
            school = School.objects.create(name=name, subscription_paid=subscription_paid)
        else:
            school = None

        return school

    @staticmethod
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


class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)

    def __unicode__(self):
        return self.username

    def change_password(self, password):
        self.password = password
        self.save()

    @staticmethod
    def create_user(base_username):
        username = User.get_valid_username(base_username)
        password = username
        return User.objects.create(username=username, password=password)

    @staticmethod
    def get_valid_username(base_username):
        username = base_username
        if User.objects.filter(username=username).exists():
            incremental = 1
            username = base_username + str(incremental)
            while User.objects.filter(username=username).exists():
                incremental += 1
                username = base_username + str(incremental)
        return username


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
        return self.first_name + " " + self.surname + " (" + self.user.username + ")"

    def get_display_items(self):
        return [self.user.username, self.first_name, self.surname]

    def delete_teacher_safe(self):
        teacher_not_used = not TeacherClassAllocation.objects.filter(teacher_id=self).exists()
        if teacher_not_used:
            self.user.delete()
            self.delete()
        return teacher_not_used

    def edit_teacher_safe(self, first_name, surname, school_id):
        self.first_name = first_name
        self.surname = surname
        self.school_id = school_id
        self.save()
        return True

    def change_password(self, password):
        self.user.change_password(password)

    @staticmethod
    def get_display_list_headings():
        return ['Username', 'First Name', 'Surname']

    @staticmethod
    def create_teacher(check_name, first_name, surname, school_id):

        if check_name:
            teacher_created = not Teacher.objects.filter(first_name=first_name, surname=surname,
                                                         school_id=school_id).exists()
        else:
            teacher_created = True

        teacher_created = teacher_created and (len(first_name) >= 1)

        if teacher_created:
            base_username = first_name[0:1] + '_' + surname
            user = User.create_user(base_username=base_username)
            teacher = Teacher.objects.create(first_name=first_name, surname=surname, school_id=school_id, user=user)
        else:
            teacher = None

        return teacher

    @staticmethod
    def update_teacher(check_name, first_name, surname, school_id):

        if check_name:
            teacher_exists = Teacher.objects.filter(first_name=first_name, surname=surname,
                                                    school_id=school_id).exists()
        else:
            teacher_exists = False

        teacher_updated = False
        if teacher_exists:
            teacher = Teacher.objects.get(first_name=first_name, surname=surname, school_id=school_id)
            teacher_updated = not ((teacher.first_name == first_name) and (teacher.surname == surname) and
                                   (teacher.school_id == school_id))
        else:
            teacher = None  # just for removing a warning

        if teacher_updated:
            teacher.first_name = first_name
            teacher.surname = surname
            teacher.school_id = school_id
            teacher.save()
            return teacher
        else:
            return None


class Administrator(models.Model):
    school_id = models.ForeignKey(School)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.user.username

    def change_password(self, password):
        self.user.change_password(password)

    @staticmethod
    def create_administrator(base_username, school_id):

        user = User.create_user(base_username=base_username)
        return Administrator.objects.create(school_id=school_id, user=user)


class Student(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female')
    )
    student_id = models.CharField(max_length=30)
    school_id = models.ForeignKey(School)
    first_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    dob = models.DateField()

    def __unicode__(self):
        return self.first_name + " " + self.surname + " (" + self.student_id + ")"

    def get_display_items(self):
        return [self.student_id, self.first_name, self.surname]

    def delete_student_safe(self):
        student_not_used = (len(StudentClassEnrolment.objects.filter(student_id=self)) == 0)
        if student_not_used:
            self.delete()
        return student_not_used

    def edit_student_safe(self, student_id, school_id, first_name, surname, gender, dob):
        is_edit_safe = ((self.student_id == student_id) and (self.school_id == school_id)) or\
                       (len(Student.objects.filter(school_id=school_id, student_id=student_id)) == 0)
        if is_edit_safe:
            self.student_id = student_id
            self.school_id = school_id
            self.first_name = first_name
            self.surname = surname
            self.gender = gender
            self.dob = dob
            self.save()
        return is_edit_safe

    @staticmethod
    def get_display_list_headings():
        return ['Student ID', 'First Name', 'Surname']

    @staticmethod
    def create_student(check_name, student_id, school_id, first_name, surname, gender, dob):

        student_unique = (len(Student.objects.filter(school_id=school_id, student_id=student_id)) == 0)
        if check_name:
            student_unique = student_unique and (len(Student.objects.filter(school_id=school_id,
                                                                            first_name=first_name,
                                                                            surname=surname)) == 0)

        if student_unique:
            Student.objects.create(student_id=student_id, school_id=school_id, first_name=first_name,
                                   surname=surname, gender=gender, dob=dob)

        return student_unique

    @staticmethod
    def update_student(check_name, student_id, school_id, first_name, surname, gender, dob):

        if check_name:
            student_exists = (len(Student.objects.filter(school_id=school_id, student_id=student_id,
                                                         first_name=first_name, surname=surname)) == 1)
        else:
            student_exists = (len(Student.objects.filter(school_id=school_id, student_id=student_id)) == 1)

        student_updated = student_exists
        if student_exists:
            student = Student.objects.get(school_id=school_id, student_id=student_id)
            student_updated = not ((student.school_id == school_id) and (student.first_name == first_name) and
                                   (student.surname == surname) and (student.gender == gender) and
                                   (student.dob == datetime.datetime.strptime(dob, "%Y-%m-%d").date()))
            if student_updated:
                student.school_id = school_id
                student.first_name = first_name
                student.surname = surname
                student.gender = gender
                student.dob = dob
                student.save()

        return student_updated


class Class(models.Model):
    year = models.IntegerField(max_length=5)
    class_name = models.CharField(max_length=200)
    school_id = models.ForeignKey(School)

    def __unicode__(self):
        return self.class_name + " (" + str(self.year) + ") - " + self.school_id.name

    def get_display_items(self):
        if TeacherClassAllocation.objects.filter(class_id=self).exists():
            allocation = TeacherClassAllocation.objects.get(class_id=self)
            teacher_display = allocation.teacher_id
        else:
            teacher_display = 'No Teacher Assigned'
        return [self.year, self.class_name, teacher_display]

    def delete_class_safe(self):
        class_not_used = (len(StudentClassEnrolment.objects.filter(class_id=self)) == 0) and\
                         (len(ClassTestSet.objects.filter(class_id=self)) == 0)
        if class_not_used:
            if len(TeacherClassAllocation.objects.filter(class_id=self)) == 1:
                allocation = TeacherClassAllocation.objects.get(class_id=self)
                allocation.delete()
            self.delete()
        return class_not_used

    def edit_class_safe(self, year, class_name, school_id, teacher_id):
        is_edit_safe = ((str(self.year) == str(year)) and (self.class_name == class_name)
                        and (self.school_id == school_id))\
            or (len(Class.objects.filter(year=year, class_name=class_name, school_id=school_id)) == 0)
        is_edit_safe = is_edit_safe and ((teacher_id is None) or (teacher_id.school_id == school_id))
        if is_edit_safe:
            if len(TeacherClassAllocation.objects.filter(class_id=self)) == 1:
                allocation = TeacherClassAllocation.objects.get(class_id=self)
                if teacher_id is None:
                    allocation.delete()
                else:
                    allocation.teacher_id = teacher_id
                    allocation.save()
            elif teacher_id is not None:
                    TeacherClassAllocation.objects.create(class_id=self, teacher_id=teacher_id)
            self.year = year
            self.class_name = class_name
            self.school_id = school_id
            self.save()
        return is_edit_safe

    def enrol_student_safe(self, student):
        enrolled = ((self.school_id == student.school_id) and
                    not StudentClassEnrolment.objects.filter(class_id=self, student_id=student).exists())
        if enrolled:
            StudentClassEnrolment.objects.create(class_id=self, student_id=student)
        return enrolled

    def withdraw_student_safe(self, student):
        withdrawn = StudentClassEnrolment.objects.filter(class_id=self, student_id=student).exists()
        if withdrawn:
            enrolment = StudentClassEnrolment.objects.get(class_id=self, student_id=student)
            withdrawn = not StudentClassTestResult.objects.filter(student_class_id=enrolment).exists()

        if withdrawn:
            StudentClassEnrolment.objects.get(class_id=self, student_id=student).delete()

        return withdrawn

    def assign_test_safe(self, test):
        assigned = not ClassTestSet.objects.filter(class_id=self, test_name=test).exists()
        if assigned:
            ClassTestSet.objects.create(class_id=self, test_name=test)
        return assigned

    def deallocate_test_safe(self, test):
        deallocate = ClassTestSet.objects.filter(class_id=self, test_name=test).exists()
        if deallocate:
            enrolments = StudentClassEnrolment.objects.filter(class_id=self)
            for enrolment in enrolments:
                deallocate = deallocate and not StudentClassTestResult.objects.filter(student_class_id=enrolment,
                                                                                      test_name=test).exists()

        if deallocate:
            ClassTestSet.objects.get(class_id=self, test_name=test).delete()

        return deallocate

    @staticmethod
    def get_display_list_headings():
        return ['Year', 'Class', 'Teacher']

    @staticmethod
    def create_class(year, class_name, school_id, teacher_id):

        class_unique = (len(Class.objects.filter(year=year, class_name=class_name, school_id=school_id)) == 0)
        teacher_in_school = (teacher_id is None) or (teacher_id.school_id == school_id)
        will_create = class_unique and teacher_in_school

        if will_create:
            class_instance = Class.objects.create(year=year, class_name=class_name, school_id=school_id)
            if teacher_id is not None:
                TeacherClassAllocation.objects.create(class_id=class_instance, teacher_id=teacher_id)

        return will_create

    @staticmethod
    def update_class(year, class_name, school_id, teacher_id):

        class_exists = (len(Class.objects.filter(year=year, class_name=class_name, school_id=school_id)) == 1)
        teacher_in_school = (teacher_id is None) or (teacher_id.school_id == school_id)

        class_updated = class_exists and teacher_in_school
        if class_exists:
            class_instance = Class.objects.get(year=year, class_name=class_name, school_id=school_id)
            teacher_is_allocated = len(TeacherClassAllocation.objects.filter(class_id=class_instance)) == 1
            teacher_is_to_be_allocated = teacher_id is not None
            if teacher_is_allocated:
                allocation = TeacherClassAllocation.objects.get(class_id=class_instance)
                class_updated = not ((str(class_instance.year) == str(year)) and
                                     (class_instance.class_name == class_name) and
                                     (class_instance.school_id == school_id) and
                                     (allocation.teacher_id == teacher_id))
            else:
                allocation = None  # just for removing a warning
                class_updated = not ((str(class_instance.year) == str(year)) and
                                     (class_instance.class_name == class_name) and
                                     (class_instance.school_id == school_id) and
                                     (not teacher_is_to_be_allocated))
            if class_updated:
                if teacher_is_allocated:
                    if teacher_is_to_be_allocated:
                        allocation.teacher_id = teacher_id
                        allocation.save()
                    else:
                        allocation.delete()
                elif teacher_is_to_be_allocated:
                    TeacherClassAllocation.objects.create(class_id=class_instance, teacher_id=teacher_id)
                class_instance.year = year
                class_instance.class_name = class_name
                class_instance.school_id = school_id
                class_instance.save()

        return class_updated


class TestCategory(models.Model):
    test_category_name = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.test_category_name

    def get_display_items(self):
        return [self.test_category_name]

    def delete_test_category_safe(self):
        test_category_not_used = not Test.objects.filter(test_category=self).exists()
        if test_category_not_used:
            self.delete()
        return test_category_not_used

    def edit_test_category_safe(self, test_category_name):
        is_edit_safe = (self.test_category_name == test_category_name)\
            or not TestCategory.objects.filter(test_category_name=test_category_name).exists()
        if is_edit_safe:
            self.test_category_name = test_category_name
            self.save()
        return is_edit_safe

    @staticmethod
    def get_display_list_headings():
        return ['Test Category']

    @staticmethod
    def create_test_category(test_category_name):
        test_category_name_unique = not TestCategory.objects.filter(test_category_name=test_category_name).exists()
        if test_category_name_unique:
            TestCategory.objects.create(test_category_name=test_category_name)
        return test_category_name_unique

    @staticmethod
    def update_test_category(test_category_name):

        test_category_updated = False

        test_category_exists = TestCategory.objects.filter(test_category_name=test_category_name).exists()
        if test_category_exists:
            test_category = TestCategory.objects.get(test_category_name=test_category_name)
            test_category_updated = not (test_category.test_category_name == test_category_name)
            if test_category_updated:
                test_category.save()

        return test_category_updated


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
    test_name = models.CharField(max_length=200, unique=True)
    test_category = models.ForeignKey(TestCategory)
    description = models.CharField(max_length=400)
    result_type = models.CharField(max_length=20, choices=RESULT_TYPE_CHOICES, default='DOUBLE')
    is_upward_percentile_brackets = models.BooleanField(default=True)
    percentile_score_conversion_type = models.CharField(max_length=20,
                                                        choices=PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES,
                                                        default='DIRECT')

    def __unicode__(self):
        return self.test_name + ' (' + self.test_category.test_category_name + ')'

    def get_display_items(self):
        return [self.test_name, self.test_category.test_category_name]

    def delete_test_safe(self):
        test_not_used = (not ClassTestSet.objects.filter(test_name=self).exists()) and\
                        (not StudentClassTestResult.objects.filter(test_name=self).exists()) and\
                        (not PercentileBracket.objects.filter(test_name=self).exists())
        if test_not_used:
            self.delete()
        return test_not_used

    def edit_test_safe(self, test_name, test_category, description, result_type,
                       is_upward_percentile_brackets, percentile_score_conversion_type):
        is_edit_safe = (self.test_name == test_name) or not Test.objects.filter(test_name=test_name).exists()
        if is_edit_safe:
            self.test_name = test_name
            self.test_category = test_category
            self.description = description
            self.result_type = result_type
            self.is_upward_percentile_brackets = is_upward_percentile_brackets
            self.percentile_score_conversion_type = percentile_score_conversion_type
            self.save()
        return is_edit_safe

    @staticmethod
    def get_display_list_headings():
        return ['Test', 'Test Category']

    @staticmethod
    def create_test(test_name, test_category, description, result_type,
                    is_upward_percentile_brackets, percentile_score_conversion_type):
        test_name_unique = not Test.objects.filter(test_name=test_name).exists()
        if test_name_unique:
            Test.objects.create(test_name=test_name, test_category=test_category, description=description,
                                result_type=result_type, is_upward_percentile_brackets=is_upward_percentile_brackets,
                                percentile_score_conversion_type=percentile_score_conversion_type)
        return test_name_unique

    @staticmethod
    def update_test(test_name, test_category, description, result_type,
                    is_upward_percentile_brackets, percentile_score_conversion_type):

        test_updated = False

        test_exists = Test.objects.filter(test_name=test_name).exists()
        if test_exists:
            test = Test.objects.get(test_name=test_name)
            test_updated = not ((test.test_name == test_name) and (test.test_category == test_category) and
                                (test.description == description) and (test.result_type == result_type) and
                                (test.is_upward_percentile_brackets == is_upward_percentile_brackets) and
                                (test.percentile_score_conversion_type == percentile_score_conversion_type))
            if test_updated:
                test.test_category = test_category
                test.description = description
                test.result_type = result_type
                test.is_upward_percentile_brackets = is_upward_percentile_brackets
                test.percentile_score_conversion_type = percentile_score_conversion_type
                test.save()

        return test_updated


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
