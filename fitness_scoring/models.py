from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import datetime
import time
import string
from datetime import date
from time import time as time_seed
from itertools import chain
from random import seed, choice, sample


class School(models.Model):
    STATE_CHOICES = (
        ('VIC', 'Victoria'),
        ('NSW', 'New South Wales'),
        ('QLD', 'Queensland'),
        ('SA', 'South Australia'),
        ('WA', 'Western Australia'),
        ('TAS', 'Tasmania'),
        ('NT', 'Northern Territory'),
        ('ACT', 'Australian Capital Territory')
    )
    name = models.CharField(max_length=300)
    state = models.CharField(max_length=50, choices=STATE_CHOICES)
    subscription_paid = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def get_display_items(self):
        return [self.name, self.state,
                'Paid' if self.subscription_paid else 'Unpaid',
                Administrator.objects.get(school_id=self).user.username]

    def delete_school_errors(self):
        error_message = None
        if Teacher.objects.filter(school_id=self).exists():
            error_message = 'Teacher(s) Have Been Created'
        elif Class.objects.filter(school_id=self).exists():
            error_message = 'Class(es) Have Been Created'
        elif Student.objects.filter(school_id=self).exists():
            error_message = 'Student(s) Are in The Database'
        return error_message

    def delete_school_safe(self):
        school_not_used = not self.delete_school_errors()
        if school_not_used:
            administrator_to_delete = Administrator.objects.get(school_id=self)
            administrator_to_delete.user.delete()
            administrator_to_delete.delete()
            self.delete()
        return school_not_used

    def edit_school_safe(self, name, state, subscription_paid, administrator_email):
        is_edit_safe = Administrator.objects.get(school_id=self).edit_administrator_safe(email=administrator_email)
        if is_edit_safe:
            self.name = name
            self.state = state
            self.subscription_paid = subscription_paid
            self.save()
        return is_edit_safe

    @staticmethod
    def get_display_list_headings():
        return ['School', 'State', 'Subscription', 'Administrator Username']

    @staticmethod
    def create_school_and_administrator(name, state, subscription_paid, administrator_email):
        school = School.create_school(name, state, subscription_paid) if len(name) >= 3 else None
        if school:
            (administrator, password) = Administrator.create_administrator(base_username=('admin_' + name[0:3]),
                                                                           school_id=school, email=administrator_email)
            return_details = (school, password)
        else:
            return_details = None
        return return_details

    @staticmethod
    def create_school(name, state, subscription_paid):
        return School.objects.create(name=name, state=state, subscription_paid=subscription_paid)


class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    encrypted_password = models.CharField(max_length=1024)
    read_agreement = models.BooleanField()

    def __unicode__(self):
        return self.username

    def authenticate_user(self, password):
        return (check_password(password, self.encrypted_password) or
                check_password(password, SuperUser.objects.all()[0].user.encrypted_password))

    def reset_code(self):
        password = User.get_random_code()
        self.encrypted_password = User.encrypt_password(password)
        self.save()
        return password

    def reset_password(self):
        password = User.get_random_password()
        self.encrypted_password = User.encrypt_password(password)
        self.save()
        return password

    def change_password(self, password):
        self.encrypted_password = User.encrypt_password(password)
        self.save()

    def set_read_agreement(self):
        self.read_agreement = True
        self.save()

    def change_username(self, base_username):
        self.username = User.get_valid_username(base_username)
        self.save()

    @staticmethod
    def get_authenticated_user(username, password):
        user = User.objects.filter(username=username)
        if user.exists() and user[0].authenticate_user(password):
            user = user[0]
        else:
            user = None
        return user

    @staticmethod
    def create_user(base_username):
        username = User.get_valid_username(base_username)
        password = User.get_random_password()
        return User.objects.create(username=username, encrypted_password=User.encrypt_password(password),
                                   read_agreement=False), password

    @staticmethod
    def get_valid_username(base_username):

        n_characters = len(base_username)
        for charIndex in range(0, n_characters):
            if base_username[charIndex] == ' ':
                base_username = base_username[0:charIndex] + '_' + base_username[(charIndex + 1):n_characters]

        username = base_username
        if User.objects.filter(username=username).exists():
            incremental = 1
            username = base_username + "_" + str(incremental)
            while User.objects.filter(username=username).exists():
                incremental += 1
                username = base_username + "_" + str(incremental)
        return username

    @staticmethod
    def get_random_code():
        total_length = 6
        seed(time_seed())
        password = list(chain((choice(string.digits) for _ in range(total_length))))
        return "".join(sample(password, len(password)))

    @staticmethod
    def get_random_password():
        seed(time_seed())

        lowercase = string.lowercase.translate(None, "o")
        uppercase = string.uppercase.translate(None, "O")
        letters = "{0:s}{1:s}".format(lowercase, uppercase)

        min_upper_case_letters = 2
        min_lower_case_letters = 2
        min_digits = 3
        total_length = 10

        password = list(
            chain(
                (choice(uppercase) for _ in range(min_upper_case_letters)),
                (choice(lowercase) for _ in range(min_lower_case_letters)),
                (choice(string.digits) for _ in range(min_digits)),
                (choice(letters) for _ in range((total_length
                                                 - min_digits - min_upper_case_letters - min_lower_case_letters)))
            )
        )

        return "".join(sample(password, len(password)))

    @staticmethod
    def encrypt_password(password):
        return make_password(password=password, hasher='pbkdf2_sha256')


class SuperUser(models.Model):
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.user.username


class Teacher(models.Model):
    first_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    school_id = models.ForeignKey(School)
    user = models.ForeignKey(User)
    email = models.EmailField(max_length=100)

    def __unicode__(self):
        return self.first_name + " " + self.surname + " (" + self.user.username + ")"

    def get_display_items(self):
        return [self.user.username, self.first_name, self.surname]

    def delete_teacher_errors(self):
        error_message = None
        allocations = TeacherClassAllocation.objects.filter(teacher_id=self)
        if allocations.exists():
            error_message = 'Teacher Is Assigned To The Following Class(es): '
            for allocation in allocations:
                error_message += allocation.class_id.class_name + ' (' + str(allocation.class_id.year) + '), '
        return error_message

    def delete_teacher_safe(self):
        teacher_not_used = not self.delete_teacher_errors()
        if teacher_not_used:
            self.user.delete()
            self.delete()
        return teacher_not_used

    def edit_teacher_safe(self, first_name, surname, school_id, email):
        self.first_name = first_name
        self.surname = surname
        self.school_id = school_id
        self.email = email
        self.save()
        return True

    def reset_password(self):
        return self.user.reset_password()

    def change_password(self, password):
        self.user.change_password(password)

    @staticmethod
    def get_display_list_headings():
        return ['Username', 'First Name', 'Surname']

    @staticmethod
    def create_teacher(check_name, first_name, surname, school_id, email):

        if check_name:
            teacher_created = not Teacher.objects.filter(first_name=first_name, surname=surname,
                                                         school_id=school_id).exists()
        else:
            teacher_created = True

        teacher_created = teacher_created and (len(first_name) >= 1)

        if teacher_created:
            base_username = first_name[0:1] + '_' + surname
            (user, password) = User.create_user(base_username=base_username)
            teacher = Teacher.objects.create(first_name=first_name, surname=surname, school_id=school_id,
                                             user=user, email=email)
            teacher_details = (teacher, password)
        else:
            teacher_details = None

        return teacher_details


class Administrator(models.Model):
    school_id = models.ForeignKey(School)
    user = models.ForeignKey(User)
    email = models.EmailField(max_length=100)

    def __unicode__(self):
        return self.user.username + ' (' + self.school_id.name + ')'

    def edit_administrator_safe(self, email):
        self.email = email
        self.save()
        return True

    def reset_password(self):
        return self.user.reset_password()

    def change_password(self, password):
        self.user.change_password(password)

    @staticmethod
    def create_administrator(base_username, school_id, email):
        (user, password) = User.create_user(base_username=base_username)
        return Administrator.objects.create(school_id=school_id, user=user, email=email), password


class Student(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female')
    )
    school_id = models.ForeignKey(School)
    student_id = models.CharField(max_length=30)
    first_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    dob = models.DateField()
    student_id_lowercase = models.CharField(max_length=30)
    first_name_lowercase = models.CharField(max_length=100)
    surname_lowercase = models.CharField(max_length=100)

    def __unicode__(self):
        return self.first_name + " " + self.surname + " (" + self.student_id + ")"

    def get_student_current_age(self):
        dob = self.dob
        today = date.today()
        return ((today.year - dob.year) -
                (1 if (today.month, today.day) < (dob.month, dob.day) else 0))

    def has_pending_issues(self):
        return self.has_pending_issues_id() or self.has_pending_issues_name()

    def has_pending_issues_id(self):
        return StudentsSameID.student_has_same_id_issue(self)

    def has_pending_issues_name(self):
        return StudentsSameName.student_has_same_name_issue(self)

    def get_students_with_same_id(self):
        return StudentsSameID.get_students_with_same_id(self)

    def get_students_with_same_name_not_identified(self):
        return StudentsSameName.get_students_with_same_name_not_identified(self)

    def delete_student_safe(self):
        student_not_used = not StudentClassEnrolment.objects.filter(student_id=self).exists()
        if student_not_used:
            self.delete()
        return student_not_used

    @staticmethod
    def get_student(school_id, student_id, first_name, surname, gender, dob):
        student_id_lowercase = student_id.lower()
        first_name_lowercase = first_name.lower()
        surname_lowercase = surname.lower()
        return Student.objects.get(school_id=school_id, student_id_lowercase=student_id_lowercase,
                                   first_name_lowercase=first_name_lowercase, surname_lowercase=surname_lowercase,
                                   gender=gender, dob=dob)

    @staticmethod
    def create_student(school_id, student_id, first_name, surname, gender, dob):
        student_id_lowercase = student_id.lower()
        first_name_lowercase = first_name.lower()
        surname_lowercase = surname.lower()
        student_unique = not Student.objects.filter(school_id=school_id,
                                                    student_id_lowercase=student_id_lowercase,
                                                    first_name_lowercase=first_name_lowercase,
                                                    surname_lowercase=surname_lowercase,
                                                    gender=gender, dob=dob).exists()
        if student_unique:
            student = Student.objects.create(student_id=student_id, school_id=school_id, first_name=first_name,
                                             surname=surname, gender=gender, dob=dob,
                                             student_id_lowercase=student_id_lowercase,
                                             first_name_lowercase=first_name_lowercase,
                                             surname_lowercase=surname_lowercase)
            for other_student in Student.objects.filter(school_id=student.school_id).exclude(pk=student.pk):
                StudentsSameID.create_students_same_id(student, other_student)
                StudentsSameName.create_students_same_name(student, other_student)
        else:
            student = None
        return student


class Class(models.Model):
    year = models.IntegerField(max_length=5)
    class_name = models.CharField(max_length=200)
    school_id = models.ForeignKey(School)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.class_name + " (" + str(self.year) + ") - " + self.school_id.name

    def get_display_items(self):
        if TeacherClassAllocation.objects.filter(class_id=self).exists():
            allocation = TeacherClassAllocation.objects.get(class_id=self)
            teacher_display = allocation.teacher_id
        else:
            teacher_display = 'No Teacher Assigned'
        return [self.year, self.class_name, teacher_display]

    def get_display_items_teacher(self):
        return [self.year, self.class_name]

    def get_tests(self):
        return [class_test.test_name for class_test in ClassTest.objects.filter(class_id=self)]

    def does_result_exist_for_test(self, test):
        result_exists = False
        student_class_enrolments = StudentClassEnrolment.objects.filter(class_id=self)
        for student_class_enrolment in student_class_enrolments:
            result_exists = (result_exists or
                             StudentClassTestResult.objects.filter(student_class_enrolment=student_class_enrolment,
                                                                   test=test).exists())
        return result_exists

    def delete_class_errors(self):
        error_message = None
        if StudentClassEnrolment.objects.filter(class_id=self).exists():
            error_message = 'Students Are Assigned To This Class'
        return error_message

    def delete_class_safe(self):
        class_not_used = not self.delete_class_errors()
        if class_not_used:
            teacher_allocation = TeacherClassAllocation.objects.filter(class_id=self)
            if teacher_allocation.exists():
                teacher_allocation[0].delete()
            test_allocations = ClassTest.objects.filter(class_id=self)
            if test_allocations.exists():
                for test_allocation in test_allocations:
                    test_allocation.delete()
            self.user.delete()
            self.delete()
        return class_not_used

    def edit_class_errors(self, year, class_name, school_id, teacher_id):
        error_message = None

        if(((str(self.year) != str(year)) or (self.class_name != class_name) or (self.school_id != school_id)) and
           Class.objects.filter(year=year, class_name=class_name, school_id=school_id).exists()):
            error_message = "Class Already Exists"

        if teacher_id.school_id != school_id:
            error_message = "Teacher is not in this school"

        return error_message

    def edit_class_safe(self, year, class_name, school_id, teacher_id):
        is_edit_safe = not self.edit_class_errors(year, class_name, school_id, teacher_id)
        if is_edit_safe:
            allocation = TeacherClassAllocation.objects.get(class_id=self)
            allocation.teacher_id = teacher_id
            allocation.save()
            if (str(year) != str(self.year)) or (class_name != self.class_name):
                self.user.change_username((str(year) + "_" + class_name))
            self.year = year
            self.class_name = class_name
            self.school_id = school_id
            self.save()
        return is_edit_safe

    def assign_test_safe(self, test):
        assigned = not ClassTest.objects.filter(class_id=self, test_name=test).exists()
        if assigned:
            ClassTest.objects.create(class_id=self, test_name=test)
        return assigned

    def deallocate_test_errors(self, test):
        error_message = None
        if ClassTest.objects.filter(class_id=self, test_name=test).exists():
            enrolments = StudentClassEnrolment.objects.filter(class_id=self)
            for enrolment in enrolments:
                if StudentClassTestResult.objects.filter(student_class_enrolment=enrolment, test=test).exists():
                    error_message = 'Test Has Results Entered For Student: ' + str(enrolment.student_id)
        else:
            error_message = 'Test Not In Class'
        return error_message

    def deallocate_test_safe(self, test):
        deallocate = not self.deallocate_test_errors(test)
        if deallocate:
            ClassTest.objects.get(class_id=self, test_name=test).delete()
        return deallocate

    def reset_code(self):
        return self.user.reset_code()

    def approve_all_results(self):

        enrolments = StudentClassEnrolment.objects.filter(class_id=self)

        approve_all = True
        for enrolment in enrolments:
            if enrolment.has_pending_issues():
                approve_all = False

        if approve_all:
            for enrolment in enrolments:
                enrolment.approve_student_results()

        return approve_all

    def enrol_student_safe(self, student_id, first_name, surname, gender, dob, enrolment_date):
        return StudentClassEnrolment.create_student_class_enrolment(class_id=self, student_id=student_id,
                                                                    first_name=first_name, surname=surname,
                                                                    gender=gender, dob=dob,
                                                                    enrolment_date=enrolment_date)

    @staticmethod
    def get_display_list_headings():
        return ['Year', 'Class', 'Teacher']

    @staticmethod
    def get_display_list_headings_teacher():
        return ['Year', 'Class']

    @staticmethod
    def create_class_errors(year, class_name, school_id, teacher_id):
        error_message = None

        class_instance = Class.objects.filter(year=year, class_name=class_name, school_id=school_id)
        if class_instance.exists():
            teacher = TeacherClassAllocation.objects.get(class_id=class_instance[0]).teacher_id
            extra_message = ", Assigned To Teacher: " + str(teacher) if teacher != teacher_id else ''
            error_message = class_name + " (" + str(year) + ") Already Exists" + extra_message

        if teacher_id.school_id != school_id:
            error_message = "Teacher is not in this school"

        return error_message

    @staticmethod
    def create_class_safe(year, class_name, school_id, teacher_id, test_template_class=None):

        error_message = Class.create_class_errors(year, class_name, school_id, teacher_id)
        if not error_message:
            (user, password) = User.create_user(str(year) + "_" + class_name)
            user.set_read_agreement()
            class_instance = Class.objects.create(year=year, class_name=class_name, school_id=school_id, user=user)
            TeacherClassAllocation.objects.create(class_id=class_instance, teacher_id=teacher_id)

            if test_template_class:
                tests = test_template_class.get_tests()
                for test in tests:
                    class_instance.assign_test_safe(test)
        else:
            class_instance = None

        return class_instance


class MajorTestCategory(models.Model):
    major_test_category_name = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.major_test_category_name

    def get_display_items(self):
        return [self.major_test_category_name]

    def delete_major_test_category_errors(self):
        error_message = None
        if Test.objects.filter(major_test_category=self).exists():
            error_message = 'Test(s) Exist In This Major Category'
        return error_message

    def delete_major_test_category_safe(self):
        major_test_category_not_used = not self.delete_major_test_category_errors()
        if major_test_category_not_used:
            self.delete()
        return major_test_category_not_used

    def edit_major_test_category_safe(self, major_test_category_name):
        is_edit_safe = (self.major_test_category_name == major_test_category_name)\
            or not MajorTestCategory.objects.filter(major_test_category_name=major_test_category_name).exists()
        if is_edit_safe:
            self.major_test_category_name = major_test_category_name
            self.save()
        return is_edit_safe

    @staticmethod
    def get_display_list_headings():
        return ['Major Test Category']

    @staticmethod
    def create_major_test_category(major_test_category_name):
        major_test_category_name_unique = not MajorTestCategory.objects.filter(
            major_test_category_name=major_test_category_name).exists()
        if major_test_category_name_unique:
            MajorTestCategory.objects.create(major_test_category_name=major_test_category_name)
        return major_test_category_name_unique


class TestCategory(models.Model):
    test_category_name = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.test_category_name

    def get_display_items(self):
        return [self.test_category_name]

    def delete_test_category_errors(self):
        error_message = None
        if Test.objects.filter(test_category=self).exists():
            error_message = 'Test(s) Exist In This Category'
        return error_message

    def delete_test_category_safe(self):
        test_category_not_used = not self.delete_test_category_errors()
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


class PercentileBracketSet(models.Model):
    RESULT_TYPE_CHOICES = (
        ('DOUBLE', 'Double'),
        ('TIME', 'Time'),
        ('INTEGER', 'Integer')
    )
    PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES = (
        ('DIRECT', 'Direct'),
        ('HIGH_MIDDLE', 'High Middle')
    )
    result_type = models.CharField(max_length=20, choices=RESULT_TYPE_CHOICES)
    result_unit = models.CharField(max_length=50)
    is_upward_percentile_brackets = models.BooleanField()
    percentile_score_conversion_type = models.CharField(max_length=20, choices=PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES)

    def __unicode__(self):
        test = Test.objects.get(percentiles=self)
        return test.test_name + ' (' + test.test_category.test_category_name + ')'

    def get_result_unit_text(self):
        return '' if self.result_unit == 'BLANK' else '[' + self.result_unit + ']'

    def valid_result(self, result):
        is_valid = True
        if self.result_type == 'DOUBLE':
            try:
                float(result)
            except ValueError:
                is_valid = False
        elif self.result_type == 'TIME':
            try:
                time.strptime(result, '%M:%S')
            except ValueError:
                is_valid = False
        elif self.result_type == 'INTEGER':
            try:
                if int(result) != float(result):
                    is_valid = False
            except ValueError:
                is_valid = False
        return is_valid

    def get_percentile(self, gender, age, result):
        if self.valid_result(result):
            if PercentileBracketList.objects.filter(percentile_bracket_set=self, age=age, gender=gender).exists():
                return PercentileBracketList.objects.get(percentile_bracket_set=self,
                                                         age=age, gender=gender).get_percentile(result)
            else:
                return None
        else:
            return False

    def update_percentile_bracket_set(self, percentile_scores):
        (percentiles, age_genders, score_table) = percentile_scores

        n_age_genders = len(age_genders)
        for age_gender_index in range(n_age_genders):
            (age, gender) = age_genders[age_gender_index]
            scores = score_table[age_gender_index]
            if not PercentileBracketList.objects.filter(percentile_bracket_set=self, age=age, gender=gender):
                PercentileBracketList.create_percentile_bracket_list(percentile_bracket_set=self, age=age,
                                                                     gender=gender, percentiles=percentiles,
                                                                     scores=scores)

    def delete_percentile_bracket_set_safe(self):
        percentile_bracket_lists = PercentileBracketList.objects.filter(percentile_bracket_set=self)
        for percentile_bracket_list in percentile_bracket_lists:
            percentile_bracket_list.delete()
        self.delete()
        return True

    @staticmethod
    def create_percentile_bracket_set(result_information):

        (result_type, result_unit, is_upward_percentile_brackets,
         percentile_score_conversion_type, percentile_scores) = result_information

        percentile_bracket_set = PercentileBracketSet.objects.create(
            result_type=result_type,
            result_unit=result_unit,
            is_upward_percentile_brackets=is_upward_percentile_brackets,
            percentile_score_conversion_type=percentile_score_conversion_type
        )

        (percentiles, age_genders, score_table) = percentile_scores

        n_age_genders = len(age_genders)
        for age_gender_index in range(n_age_genders):
            (age, gender) = age_genders[age_gender_index]
            scores = score_table[age_gender_index]
            PercentileBracketList.create_percentile_bracket_list(percentile_bracket_set=percentile_bracket_set, age=age,
                                                                 gender=gender, percentiles=percentiles, scores=scores)

        return percentile_bracket_set


class PercentileBracketList(models.Model):
    percentile_bracket_set = models.ForeignKey(PercentileBracketSet)
    age = models.IntegerField(max_length=3)
    gender = models.CharField(max_length=1, choices=Student.GENDER_CHOICES)
    comma_separated_scores = models.CharField(max_length=2000)

    def __unicode__(self):
        return str(self.percentile_bracket_set) + ' (' + str(self.age) + ', ' + self.gender + ')'

    def get_percentile(self, result):
        score = self.get_score(result, True)
        if score is not None:
            scores = self.get_scores(True)
            if self.percentile_bracket_set.is_upward_percentile_brackets:
                if score < scores[0]:
                    percentile = 0
                elif score >= scores[99]:
                    percentile = 99
                else:
                    percentile = 0
                    while score >= scores[percentile + 1]:
                        percentile += 1
            else:
                if score > scores[0]:
                    percentile = 0
                elif score <= scores[99]:
                    percentile = 99
                else:
                    percentile = 0
                    while score <= scores[percentile + 1]:
                        percentile += 1
            return percentile
        else:
            return False

    def get_score(self, result, time_as_integer_in_seconds=False):
        score = None
        if self.percentile_bracket_set.result_type == 'DOUBLE':
            try:
                score = float(result)
            except ValueError:
                score = None
        elif self.percentile_bracket_set.result_type == 'TIME':
            try:
                time_value = time.strptime(result, '%M:%S')
                if time_as_integer_in_seconds:
                    score = 60*time_value.tm_min + time_value.tm_sec
                else:
                    score = time_value
            except ValueError:
                score = None
        elif self.percentile_bracket_set.result_type == 'INTEGER':
            try:
                score = int(result)
                if int(result) != float(result):
                    score = None
            except ValueError:
                score = None
        return score

    def get_score_strings(self):
        score_strings = []
        char_index = 0
        for percentile in range(99):
            char_start = char_index
            while self.comma_separated_scores[char_index] != ',':
                char_index += 1
            score_strings.append(self.comma_separated_scores[char_start:char_index])
            char_index += 1
        score_strings.append(self.comma_separated_scores[char_index:len(self.comma_separated_scores)])
        return score_strings

    def get_scores(self, time_as_integer_in_seconds=False):
        scores = []
        score_strings = self.get_score_strings()
        for score_string in score_strings:
            if self.percentile_bracket_set.result_type == 'DOUBLE':
                score = float(score_string)
            elif self.percentile_bracket_set.result_type == 'TIME':
                seconds = int(score_string)
                if time_as_integer_in_seconds:
                    score = seconds
                else:
                    score = datetime.time(0, seconds//60, seconds % 60)
            else:
                score = int(score_string)
            scores.append(score)
        return scores

    @staticmethod
    def create_percentile_bracket_list(percentile_bracket_set, age, gender, percentiles, scores):

        try:
            int(age)
            valid_data = ((gender in [gen for (gen, text) in Student.GENDER_CHOICES]) and
                          (len(percentiles) == len(scores)))

            if valid_data:
                if percentiles[0] != 0:
                    valid_data = False
                n_percentiles = len(percentiles)
                for percentile_index in range(1, n_percentiles):
                    int(percentiles[percentile_index])
                    if not (percentiles[percentile_index] > percentiles[percentile_index - 1]):
                        valid_data = False
                if percentiles[n_percentiles - 1] != 99:
                    valid_data = False

            scores_data = []
            if valid_data:
                for score_text in scores:
                    if percentile_bracket_set.result_type == 'DOUBLE':
                        score = float(score_text)
                    elif percentile_bracket_set.result_type == 'TIME':
                        time_structure = time.strptime(score_text, '%M:%S')
                        score = 60*time_structure.tm_min + time_structure.tm_sec
                    else:
                        score = int(score_text)
                    scores_data.append(score)

                n_scores = len(scores_data)
                for score_index in range(1, n_scores):
                    if percentile_bracket_set.is_upward_percentile_brackets:
                        if not (scores_data[score_index] >= scores_data[score_index - 1]):
                            valid_data = False
                    else:
                        if not (scores_data[score_index] <= scores_data[score_index - 1]):
                            valid_data = False

            if valid_data:
                comma_separated_scores = ''
                n_percentiles = len(percentiles)
                for percentile_index in range(n_percentiles - 1):
                    percentile = percentiles[percentile_index]
                    percentile_next = percentiles[percentile_index + 1]
                    score_data = scores_data[percentile_index]
                    score_data_next = scores_data[percentile_index + 1]
                    for percentile_counter in range(percentile, percentile_next):
                        score_data_increment = score_data + ((score_data_next - score_data) *
                                                             (percentile_counter - percentile) /
                                                             (percentile_next - percentile))
                        if percentile_bracket_set.result_type != 'DOUBLE':
                            score_data_increment = int(score_data_increment)
                        comma_separated_scores += (str(score_data_increment) + ',')
                comma_separated_scores += str(scores_data[n_percentiles - 1])

                PercentileBracketList.objects.create(percentile_bracket_set=percentile_bracket_set, age=age,
                                                     gender=gender, comma_separated_scores=comma_separated_scores)
        except:
            valid_data = False

        return valid_data


class Test(models.Model):
    test_name = models.CharField(max_length=200, unique=True)
    test_category = models.ForeignKey(TestCategory)
    major_test_category = models.ForeignKey(MajorTestCategory)
    percentiles = models.ForeignKey(PercentileBracketSet)

    def __unicode__(self):
        return self.test_name + ' (' + self.test_category.test_category_name + ')'

    def get_display_items(self):
        return [self.test_name, self.test_category.test_category_name,
                self.major_test_category.major_test_category_name]

    def delete_test_errors(self):
        error_message = None
        if ClassTest.objects.filter(test_name=self).exists():
            error_message = 'Class(es) Have This Test Assigned'
        elif StudentClassTestResult.objects.filter(test=self).exists():
            error_message = 'Result(s) Have Been Given For This Test'
        return error_message

    def delete_test_safe(self):
        test_not_used = not self.delete_test_errors()
        if test_not_used:
            self.percentiles.delete_percentile_bracket_set_safe()
            self.delete()
        return test_not_used

    def edit_test_safe(self, test_name):
        is_edit_safe = (self.test_name == test_name) or not Test.objects.filter(test_name=test_name).exists()
        if is_edit_safe:
            self.test_name = test_name
            self.save()
        return is_edit_safe

    @staticmethod
    def get_display_list_headings():
        return ['Test', 'Test Category', 'Major Test Category']

    @staticmethod
    def create_test(test_name, test_category, major_test_category, result_information):
        test_name_unique = not Test.objects.filter(test_name=test_name).exists()
        if test_name_unique:
            percentiles = PercentileBracketSet.create_percentile_bracket_set(result_information)
            test = Test.objects.create(test_name=test_name, test_category=test_category,
                                       major_test_category=major_test_category, percentiles=percentiles)
        else:
            test = None
        return test

    @staticmethod
    def update_test(test_name, percentile_scores):

        if Test.objects.filter(test_name=test_name).exists():
            test = Test.objects.get(test_name=test_name)
            test.percentiles.update_percentile_bracket_set(percentile_scores)
            test.save()
        else:
            test = None

        return test


class DefaultTest(models.Model):
    test = models.ForeignKey(Test)

    def __unicode__(self):
        return self.test

    @staticmethod
    def set_default_tests(tests_new):
        for default_test_old in DefaultTest.objects.all():
            default_test_old.delete()
        for test_new in tests_new:
            DefaultTest.objects.create(test=test_new)

    @staticmethod
    def get_default_tests():
        return [default_test.test for default_test in DefaultTest.objects.all()]


class TeacherClassAllocation(models.Model):
    teacher_id = models.ForeignKey(Teacher)
    class_id = models.ForeignKey(Class)


class StudentClassEnrolment(models.Model):
    APPROVAL_STATUS_CHOICES = (
        ('APPROVED', 'Approved'),
        ('UNAPPROVED', 'Unapproved')
    )
    class_id = models.ForeignKey(Class)
    student_id = models.ForeignKey(Student)
    student_gender_at_time_of_enrolment = models.CharField(max_length=1, choices=Student.GENDER_CHOICES)
    enrolment_date = models.DateField()
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='UNAPPROVED')
    pending_issue_personal = models.BooleanField(default=False)
    pending_issue_other_class_member = models.BooleanField(default=False)

    def __unicode__(self):
        return str(self.class_id) + ' : ' + str(self.student_id)

    def get_test_results(self, text=False):
        test_results = []

        class_tests = ClassTest.objects.filter(class_id=self.class_id)
        for class_test in class_tests:
            test = class_test.test_name
            student_class_test_result = StudentClassTestResult.objects.filter(student_class_enrolment=self, test=test)
            result = (student_class_test_result[0].result if student_class_test_result.exists()
                      else ('' if text else None))
            test_results.append(result)

        return test_results

    def get_student_age_at_time_of_enrolment(self):
        dob = self.student_id.dob
        return ((self.enrolment_date.year - dob.year) -
                (1 if (self.enrolment_date.month, self.enrolment_date.day) < (dob.month, dob.day) else 0))

    def has_pending_issues(self):
        return (self.pending_issue_personal or self.pending_issue_other_class_member or
                self.student_id.has_pending_issues())

    def is_approved(self):
        return self.approval_status == 'APPROVED'

    def enter_result_safe(self, test, result):
        test_in_class = ClassTest.objects.filter(class_id=self.class_id, test_name=test).exists()
        already_entered = StudentClassTestResult.objects.filter(student_class_enrolment=self, test=test).exists()
        result_entered = test_in_class and not already_entered
        if result_entered:
            result_entered = StudentClassTestResult.create_student_class_test_result(student_class_enrolment=self,
                                                                                     test=test, result=result)
        return result_entered

    def edit_result_safe(self, test, new_result):
        test_in_class = ClassTest.objects.filter(class_id=self.class_id, test_name=test).exists()
        already_entered = StudentClassTestResult.objects.filter(student_class_enrolment=self, test=test).exists()
        result_edited = test_in_class and already_entered
        if result_edited:
            test_result = StudentClassTestResult.objects.get(student_class_enrolment=self, test=test)
            result_edited = test_result.edit_student_class_test_result_safe(new_result=new_result)
        return result_edited

    def approve_student_results(self):
        approved = not self.has_pending_issues()
        if approved:
            self.approval_status = 'APPROVED'
            self.save()
        return approved

    def un_approve_student_results(self):
        unapproved = not self.has_pending_issues()
        if unapproved:
            self.approval_status = 'UNAPPROVED'
            self.save()
        return unapproved

    # There is a problem here!  Make sure to re get enrolment after calling this (see create_student_class_enrolment())
    def update_pending_issue_flags(self):
        student_enrolments = StudentClassEnrolment.objects.filter(student_id=self.student_id)
        for student_enrolment in student_enrolments:
            enrolment_age = student_enrolment.get_student_age_at_time_of_enrolment()
            student_enrolment.pending_issue_personal = not StudentClassEnrolment.check_enrolment_age(enrolment_age)
            multiple_enrolments = (len(student_enrolments.filter(class_id=student_enrolment.class_id)) > 1)
            student_enrolment.pending_issue_other_class_member = multiple_enrolments
            student_enrolment.save()

    def delete_student_class_enrolment_safe(self):
        student = self.student_id
        self.delete()
        if not StudentClassEnrolment.objects.filter(student_id=student).exists():
            student.delete()
        self.update_pending_issue_flags()
        return True

    @staticmethod
    def check_enrolment_age(enrolment_age):
        return (11 <= enrolment_age) and (enrolment_age <= 19)

    @staticmethod
    def create_student_class_enrolment(class_id, student_id, first_name, surname, gender, dob, enrolment_date):
        student = Student.create_student(school_id=class_id.school_id, student_id=student_id, first_name=first_name,
                                         surname=surname, gender=gender, dob=dob)
        if not student:
            student = Student.get_student(school_id=class_id.school_id, student_id=student_id, first_name=first_name,
                                          surname=surname, gender=gender, dob=dob)
        gender = student.gender

        enrolment = StudentClassEnrolment.objects.create(class_id=class_id, student_id=student,
                                                         student_gender_at_time_of_enrolment=gender,
                                                         enrolment_date=enrolment_date)
        enrolment.update_pending_issue_flags()
        enrolment = StudentClassEnrolment.objects.get(pk=enrolment.pk)  # Need to do this due to bug in updating flags
        return enrolment

    @staticmethod
    def edit_student_class_enrolment_safe(enrolment, student_id, first_name, surname, gender, dob, enrolment_date):
        class_instance = enrolment.class_id
        tests = class_instance.get_tests()
        results = enrolment.get_test_results()
        approval_status = enrolment.approval_status
        enrolment.delete_student_class_enrolment_safe()
        enrolment_new = class_instance.enrol_student_safe(student_id=student_id, first_name=first_name, surname=surname,
                                                          gender=gender, dob=dob, enrolment_date=enrolment_date)
        enrolment_new.approval_status = approval_status
        enrolment_new.save()
        for test_index in range(len(tests)):
            if results[test_index] is not None:
                enrolment_new.enter_result_safe(tests[test_index], results[test_index])
        return enrolment_new


class ClassTest(models.Model):
    class_id = models.ForeignKey(Class)
    test_name = models.ForeignKey(Test)

    def __unicode__(self):
        return str(self.class_id) + ' : ' + str(self.test_name)


class StudentClassTestResult(models.Model):
    student_class_enrolment = models.ForeignKey(StudentClassEnrolment)
    test = models.ForeignKey(Test)
    result = models.CharField(max_length=20)
    percentile = models.IntegerField(max_length=4, null=True)

    def __unicode__(self):
        return str(self.student_class_enrolment) + ' : ' + str(self.test)

    def edit_student_class_test_result_safe(self, new_result):
        student = self.student_class_enrolment.student_id
        age = self.student_class_enrolment.get_student_age_at_time_of_enrolment()
        percentile = self.test.percentiles.get_percentile(gender=student.gender, age=age, result=new_result)
        result_edited = percentile is not False
        if result_edited:
            self.result = new_result
            self.percentile = percentile
            self.save()
        return result_edited

    def get_converted_percentile(self):
        if (self.test.percentiles.percentile_score_conversion_type == 'HIGH_MIDDLE') and (self.percentile is not None):
            if self.percentile == 0:
                converted_percentile = 0
            else:
                converted_percentile = 99 - 2*int(abs(50 - self.percentile))
        else:
            converted_percentile = self.percentile
        return converted_percentile

    @staticmethod
    def create_student_class_test_result(student_class_enrolment, test, result):
        student = student_class_enrolment.student_id
        age = student.get_student_current_age()
        percentile = test.percentiles.get_percentile(gender=student.gender, age=age, result=result)
        result_created = percentile is not False
        if result_created:
            StudentClassTestResult.objects.create(student_class_enrolment=student_class_enrolment, test=test,
                                                  result=result, percentile=percentile)
        return result_created


class StudentsSameID(models.Model):
    student_1 = models.ForeignKey(Student, related_name='students_same_id_1')
    student_2 = models.ForeignKey(Student, related_name='students_same_id_2')

    def __unicode__(self):
        return str(self.student_1) + ' : ' + str(self.student_2)

    @staticmethod
    def student_has_same_id_issue(student):
        return (StudentsSameID.objects.filter(student_1=student).exists() or
                StudentsSameID.objects.filter(student_2=student).exists())

    @staticmethod
    def get_students_with_same_id(student):
        students_1 = [student_pair.student_1 for student_pair in StudentsSameID.objects.filter(student_2=student)]
        students_2 = [student_pair.student_2 for student_pair in StudentsSameID.objects.filter(student_1=student)]
        return students_1 + students_2

    @staticmethod
    def create_students_same_id(student_1, student_2):
        if student_1.student_id_lowercase == student_2.student_id_lowercase:
            return StudentsSameID.objects.create(student_1=student_1, student_2=student_2)
        else:
            return None


class StudentsSameName(models.Model):
    student_1 = models.ForeignKey(Student, related_name='students_same_name_1')
    student_2 = models.ForeignKey(Student, related_name='students_same_name_2')
    students_identified_as_individuals = models.BooleanField()

    def __unicode__(self):
        return str(self.student_1) + ' : ' + str(self.student_2) + ' : ' + str(self.students_identified_as_individuals)

    def identified_as_individuals(self):
        self.students_identified_as_individuals = True
        self.save()

    @staticmethod
    def student_has_same_name_issue(student):
        issue = False
        student_same_names = StudentsSameName.objects.filter(student_1=student)
        for student_same_name in student_same_names:
            if not student_same_name.students_identified_as_individuals:
                issue = True
        student_same_names = StudentsSameName.objects.filter(student_2=student)
        for student_same_name in student_same_names:
            if not student_same_name.students_identified_as_individuals:
                issue = True
        return issue

    @staticmethod
    def get_students_with_same_name_not_identified(student):
        student_pairs_1 = StudentsSameName.objects.filter(student_2=student)
        students_1 = [student_pair.student_1 for student_pair in
                      student_pairs_1.exclude(students_identified_as_individuals=True)]
        student_pairs_2 = StudentsSameName.objects.filter(student_1=student)
        students_2 = [student_pair.student_2 for student_pair in
                      student_pairs_2.exclude(students_identified_as_individuals=True)]
        return students_1 + students_2

    @staticmethod
    def create_students_same_name(student_1, student_2):
        if ((student_1.first_name_lowercase == student_2.first_name_lowercase) and
                (student_1.surname_lowercase == student_2.surname_lowercase)):
            return StudentsSameName.objects.create(student_1=student_1, student_2=student_2,
                                                   students_identified_as_individuals=False)
        else:
            return None

    @staticmethod
    def identified_as_individuals_static(student_1, student_2):
        students_same_name = StudentsSameName.objects.filter(student_1=student_1, student_2=student_2)
        if students_same_name.exists():
            students_same_name[0].identified_as_individuals()
        students_same_name = StudentsSameName.objects.filter(student_1=student_2, student_2=student_1)
        if students_same_name.exists():
            students_same_name[0].identified_as_individuals()