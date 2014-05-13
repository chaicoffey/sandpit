from django.db import models
import datetime
import time
import collections
import string
from time import time as time_seed
from itertools import chain
from random import seed, choice, sample
import random
from hashlib import sha1


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

    def edit_school_safe(self, name, subscription_paid, administrator_email):
        is_edit_safe = (self.name == name) or (len(School.objects.filter(name=name)) == 0)
        if is_edit_safe:
            Administrator.objects.get(school_id=self).edit_administrator_safe(email=administrator_email)
            self.name = name
            self.subscription_paid = subscription_paid
            self.save()
        return is_edit_safe

    @staticmethod
    def get_display_list_headings():
        return ['School Name', 'Subscription', 'Administrator Username']

    @staticmethod
    def create_school_and_administrator(name, subscription_paid, administrator_email):
        school = School.create_school(name, subscription_paid) if len(name) >= 3 else None
        if school:
            (administrator, password) = Administrator.create_administrator(base_username=('admin_' + name[0:3]),
                                                                           school_id=school, email=administrator_email)
            return_details = (school, password)
        else:
            return_details = None
        return return_details

    @staticmethod
    def create_school(name, subscription_paid):

        if not School.objects.filter(name=name).exists():
            school = School.objects.create(name=name, subscription_paid=subscription_paid)
        else:
            school = None

        return school

    @staticmethod
    def update_school(name, subscription_paid, administrator_email):

        school_updated = False

        school_name_exists = (len(School.objects.filter(name=name)) == 1)
        if school_name_exists:
            school = School.objects.get(name=name)
            administrator = Administrator.objects.get(school_id=school)
            school_updated = not ((school.subscription_paid == subscription_paid) and
                                  (administrator.email == administrator_email))
            if school_updated:
                administrator.edit_administrator_safe(email=administrator_email)
                school.subscription_paid = subscription_paid
                school.save()

        return school_updated


class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    encrypted_password = models.CharField(max_length=1024)

    def __unicode__(self):
        return self.username

    def authenticate_user(self, password):
        salt, hsh = self.encrypted_password.split('$')
        return hsh == sha1('%s%s' % (salt, password)).hexdigest()

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
        return User.objects.create(username=username, encrypted_password=User.encrypt_password(password)), password

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
        salt = sha1('%s%s' % (str(random.random()), str(random.random()))).hexdigest()[:5]
        hsh = sha1('%s%s' % (salt, password)).hexdigest()
        return '%s$%s' % (salt, hsh)


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

    def delete_teacher_safe(self):
        teacher_not_used = not TeacherClassAllocation.objects.filter(teacher_id=self).exists()
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

    def delete_class_safe(self):
        class_not_used = not StudentClassEnrolment.objects.filter(class_id=self).exists()
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

    def save_class_tests_as_test_set_errors(self, test_set_name):
        return TestSet.create_test_set_errors(test_set_name, self.school_id, self.get_tests())

    def save_class_tests_as_test_set_safe(self, test_set_name):
        return TestSet.create_test_set(test_set_name, self.school_id, self.get_tests())

    def load_class_tests_from_test_set_errors(self, test_set_name):

        if TestSet.objects.filter(school=self.school_id, test_set_name=test_set_name).exists():
            error_message = None
        else:
            error_message = 'No Test Set Exists With Name: ' + test_set_name

        if not error_message:
            test_set_tests = TestSet.objects.get(school=self.school_id, test_set_name=test_set_name).get_tests()
            class_tests = self.get_tests()
            for class_test in class_tests:
                if (not (class_test in test_set_tests)) and self.does_result_exist_for_test(test=class_test):
                    error_message = ('Test ' + class_test.test_name + ' has results entered but is not in test set ' +
                                     test_set_name)

        return error_message

    def load_class_tests_from_test_set_safe(self, test_set_name):
        load_valid = not self.load_class_tests_from_test_set_errors(test_set_name)
        if load_valid:

            test_set_tests = TestSet.objects.get(school=self.school_id, test_set_name=test_set_name).get_tests()
            class_tests = self.get_tests()
            for class_test in class_tests:
                if not (class_test in test_set_tests):
                    ClassTest.objects.get(class_id=self, test_name=class_test).delete()
            for test_set_test in test_set_tests:
                if not (test_set_test in class_tests):
                    ClassTest.objects.create(class_id=self, test_name=test_set_test)

        return load_valid

    def deallocate_test_safe(self, test):
        deallocate = ClassTest.objects.filter(class_id=self, test_name=test).exists()
        if deallocate:
            enrolments = StudentClassEnrolment.objects.filter(class_id=self)
            for enrolment in enrolments:
                deallocate = deallocate and not StudentClassTestResult.objects.filter(student_class_id=enrolment,
                                                                                      test_name=test).exists()

        if deallocate:
            ClassTest.objects.get(class_id=self, test_name=test).delete()

        return deallocate

    def reset_code(self):
        return self.user.reset_code()

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

    @staticmethod
    def get_display_list_headings():
        return ['Year', 'Class', 'Teacher']

    @staticmethod
    def get_display_list_headings_teacher():
        return ['Year', 'Class']

    @staticmethod
    def create_class_errors(year, class_name, school_id, teacher_id):
        error_message = None

        if Class.objects.filter(year=year, class_name=class_name, school_id=school_id).exists():
            error_message = "Class Already Exists"

        if teacher_id.school_id != school_id:
            error_message = "Teacher is not in this school"

        return error_message

    @staticmethod
    def create_class_safe(year, class_name, school_id, teacher_id):

        error_message = Class.create_class_errors(year, class_name, school_id, teacher_id)
        if not error_message:
            (user, password) = User.create_user(str(year) + "_" + class_name)
            class_instance = Class.objects.create(year=year, class_name=class_name, school_id=school_id, user=user)
            TeacherClassAllocation.objects.create(class_id=class_instance, teacher_id=teacher_id)
        else:
            class_instance = None

        return class_instance


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
    is_upward_percentile_brackets = models.BooleanField()
    percentile_score_conversion_type = models.CharField(max_length=20, choices=PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES)

    def __unicode__(self):
        test = Test.objects.get(percentiles=self)
        return test.test_name + ' (' + test.test_category.test_category_name + ')'

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

        (result_type, is_upward_percentile_brackets,
         percentile_score_conversion_type, percentile_scores) = result_information

        percentile_bracket_set = PercentileBracketSet.objects.create(
            result_type=result_type,
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
                        if not (scores_data[score_index] > scores_data[score_index - 1]):
                            valid_data = False
                    else:
                        if not (scores_data[score_index] < scores_data[score_index - 1]):
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
    percentiles = models.ForeignKey(PercentileBracketSet)

    def __unicode__(self):
        return self.test_name + ' (' + self.test_category.test_category_name + ')'

    def get_display_items(self):
        return [self.test_name, self.test_category.test_category_name]

    def delete_test_safe(self):
        test_not_used = ((not ClassTest.objects.filter(test_name=self).exists()) and
                         (not StudentClassTestResult.objects.filter(test=self).exists()))
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
        return ['Test', 'Test Category']

    @staticmethod
    def create_test(test_name, test_category, result_information):
        test_name_unique = not Test.objects.filter(test_name=test_name).exists()
        if test_name_unique:
            percentiles = PercentileBracketSet.create_percentile_bracket_set(result_information)
            test = Test.objects.create(test_name=test_name, test_category=test_category, percentiles=percentiles)
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


class TeacherClassAllocation(models.Model):
    teacher_id = models.ForeignKey(Teacher)
    class_id = models.ForeignKey(Class)


class StudentClassEnrolment(models.Model):
    class_id = models.ForeignKey(Class)
    student_id = models.ForeignKey(Student)
    student_age_at_time_of_enrolment = models.IntegerField(max_length=4)

    def get_test_results(self):
        test_results = []

        class_tests = ClassTest.objects.filter(class_id=self.class_id)
        for class_test in class_tests:
            test = class_test.test_name
            student_class_test_result = StudentClassTestResult.objects.filter(student_class_enrolment=self, test=test)
            result = student_class_test_result[0].result if student_class_test_result.exists() else None
            test_results.append(result)

        return test_results
    

class ClassTest(models.Model):
    class_id = models.ForeignKey(Class)
    test_name = models.ForeignKey(Test)


class TestSet(models.Model):
    school = models.ForeignKey(School)
    test_set_name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.test_set_name + ' (' + self.school.name + ')'

    def get_tests(self):
        return [test_set_test.test for test_set_test in TestSetTest.objects.filter(test_set=self)]

    @staticmethod
    def create_test_set_errors(test_set_name, school, tests):
        error_message = None

        if TestSet.objects.filter(school=school, test_set_name=test_set_name).exists():
            error_message = 'Test Set Name Already Being Used'

        if not error_message:
            test_sets = TestSet.objects.filter(school=school)
            for test_set in test_sets:
                if collections.Counter(test_set.get_tests()) == collections.Counter(tests):
                    error_message = ("Test Set Comprised Of The Same Tests Already Exists (" + test_set.test_set_name +
                                     ")")

        return error_message

    @staticmethod
    def create_test_set(test_set_name, school, tests):
        if not TestSet.create_test_set_errors(test_set_name, school, tests):
            test_set = TestSet.objects.create(school=school, test_set_name=test_set_name)
            for test in tests:
                TestSetTest.objects.create(test_set=test_set, test=test)
        else:
            test_set = None

        return test_set


class TestSetTest(models.Model):
    test_set = models.ForeignKey(TestSet)
    test = models.ForeignKey(Test)


class StudentClassTestResult(models.Model):
    student_class_enrolment = models.ForeignKey(StudentClassEnrolment)
    test = models.ForeignKey(Test)
    result = models.CharField(max_length=20)
    percentile = models.IntegerField(max_length=4)
