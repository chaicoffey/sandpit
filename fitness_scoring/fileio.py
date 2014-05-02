import csv
import tempfile
import os
from fitness_scoring.models import Student, Teacher, Class, School, User, TestCategory, Test, PercentileBracketSet

destination_directory = 'C:\\fitness_scoring_file_uploads\\'
#destination_directory = '/tmp/fitness_scoring_file_uploads'


def save_file(f):
    destination_file = tempfile.NamedTemporaryFile(dir=destination_directory, delete=False)
    destination_file.seek(0)
    for chunk in f.chunks():
        destination_file.write(chunk)
    destination_file.flush()
    destination_file.close()
    return destination_file.name


def delete_file(file_name):
    os.remove(file_name)


def add_students_from_file_upload(uploaded_file, school_id):
    file_path_on_server = save_file(uploaded_file)
    (n_created, n_updated, n_not_created_or_updated) = add_students_from_file(file_path_on_server, school_id)
    delete_file(file_path_on_server)
    return n_created, n_updated, n_not_created_or_updated


def add_students_from_file(file_path_on_server, school_id):
    file_handle = open(file_path_on_server, 'rb')

    dialect = csv.Sniffer().sniff(file_handle.read(1024))
    dialect.strict = True

    file_handle.seek(0)
    students_list_reader = csv.DictReader(file_handle, dialect=dialect)
    # check headings are correct else throw exception

    n_created = 0
    n_updated = 0
    n_not_created_or_updated = 0
    for line in students_list_reader:
        (student_id, first_name, surname, gender, dob) = (line['student_id'], line['first_name'], line['surname'],
                                                          line['gender'], line['dob'])
        if Student.create_student(check_name=False, student_id=student_id, school_id=school_id,
                                  first_name=first_name, surname=surname, gender=gender, dob=dob):
            n_created += 1
        elif Student.update_student(check_name=False, student_id=student_id, school_id=school_id,
                                    first_name=first_name, surname=surname, gender=gender, dob=dob):
            n_updated += 1
        else:
            n_not_created_or_updated += 1

    return n_created, n_updated, n_not_created_or_updated


def add_teachers_from_file_upload(uploaded_file, school_id):
    file_path_on_server = save_file(uploaded_file)
    (n_created, n_updated, n_not_created_or_updated) = add_teachers_from_file(file_path_on_server, school_id)
    delete_file(file_path_on_server)
    return n_created, n_updated, n_not_created_or_updated


def add_teachers_from_file(file_path_on_server, school_id):
    file_handle = open(file_path_on_server, 'rb')

    dialect = csv.Sniffer().sniff(file_handle.read(1024))
    dialect.strict = True

    file_handle.seek(0)
    teachers_list_reader = csv.DictReader(file_handle, dialect=dialect)
    # check headings are correct else throw exception

    n_created = 0
    n_updated = 0
    n_not_created_or_updated = 0
    for line in teachers_list_reader:
        (first_name, surname) = (line['first_name'], line['surname'])
        if Teacher.create_teacher(check_name=True, first_name=first_name, surname=surname,
                                  school_id=school_id):
            n_created += 1
        elif Teacher.update_teacher(check_name=False, first_name=first_name, surname=surname,
                                    school_id=school_id):
            n_updated += 1
        else:
            n_not_created_or_updated += 1

    return n_created, n_updated, n_not_created_or_updated


def add_classes_from_file_upload(uploaded_file, school_id):
    file_path_on_server = save_file(uploaded_file)
    (n_created, n_updated, n_not_created_or_updated) = add_classes_from_file(file_path_on_server, school_id)
    delete_file(file_path_on_server)
    return n_created, n_updated, n_not_created_or_updated


def add_classes_from_file(file_path_on_server, school_id):
    file_handle = open(file_path_on_server, 'rb')

    dialect = csv.Sniffer().sniff(file_handle.read(1024))
    dialect.strict = True

    file_handle.seek(0)
    classes_list_reader = csv.DictReader(file_handle, dialect=dialect)
    # check headings are correct else throw exception

    n_created = 0
    n_updated = 0
    n_not_created_or_updated = 0
    for line in classes_list_reader:
        (year, class_name, teacher_username) = (line['year'], line['class_name'], line['teacher_username'])
        teacher_id = (
            Teacher.objects.get(user=User.objects.get(username=teacher_username))
            if User.objects.filter(username=teacher_username).exists() and
               Teacher.objects.filter(user=User.objects.get(username=teacher_username), school_id=school_id).exists()
            else None
        )

        if Class.create_class(year=year, class_name=class_name, school_id=school_id, teacher_id=teacher_id):
            n_created += 1
        elif Class.update_class(year=year, class_name=class_name, school_id=school_id, teacher_id=teacher_id):
            n_updated += 1
        else:
            n_not_created_or_updated += 1

    return n_created, n_updated, n_not_created_or_updated


def enrol_students_in_class_from_file_upload(uploaded_file, class_instance):
    file_path_on_server = save_file(uploaded_file)
    (n_created, n_not_created) = enrol_students_in_class_from_file(file_path_on_server, class_instance)
    delete_file(file_path_on_server)
    return n_created, 0, n_not_created


def enrol_students_in_class_from_file(file_path_on_server, class_instance):
    file_handle = open(file_path_on_server, 'rb')

    dialect = csv.Sniffer().sniff(file_handle.read(1024))
    dialect.strict = True

    file_handle.seek(0)
    classes_list_reader = csv.DictReader(file_handle, dialect=dialect)
    # check headings are correct else throw exception

    school = class_instance.school_id

    n_created = 0
    n_not_created = 0
    for line in classes_list_reader:
        (student_id) = (line['student_id'])
        student = (Student.objects.get(student_id=student_id, school_id=school)
                   if Student.objects.filter(student_id=student_id, school_id=school).exists()
                   else None)

        if student and class_instance.enrol_student_safe(student):
            n_created += 1
        else:
            n_not_created += 1

    return n_created, n_not_created


def assign_tests_to_class_from_file_upload(uploaded_file, class_instance):
    file_path_on_server = save_file(uploaded_file)
    (n_created, n_not_created) = assign_tests_to_class_from_file(file_path_on_server, class_instance)
    delete_file(file_path_on_server)
    return n_created, 0, n_not_created


def assign_tests_to_class_from_file(file_path_on_server, class_instance):
    file_handle = open(file_path_on_server, 'rb')

    dialect = csv.Sniffer().sniff(file_handle.read(1024))
    dialect.strict = True

    file_handle.seek(0)
    classes_list_reader = csv.DictReader(file_handle, dialect=dialect)
    # check headings are correct else throw exception

    n_created = 0
    n_not_created = 0
    for line in classes_list_reader:
        (test_name) = (line['test_name'])
        test = Test.objects.get(test_name=test_name) if Test.objects.filter(test_name=test_name).exists() else None

        if test and class_instance.assign_test_safe(test):
            n_created += 1
        else:
            n_not_created += 1

    return n_created, n_not_created


def add_schools_from_file_upload(uploaded_file):
    file_path_on_server = save_file(uploaded_file)
    (n_created, n_updated, n_not_created_or_updated) = add_schools_from_file(file_path_on_server)
    delete_file(file_path_on_server)
    return n_created, n_updated, n_not_created_or_updated


def add_schools_from_file(file_path_on_server):
    file_handle = open(file_path_on_server, 'rb')

    dialect = csv.Sniffer().sniff(file_handle.read(1024))
    dialect.strict = True

    file_handle.seek(0)
    schools_list_reader = csv.DictReader(file_handle, dialect=dialect)
    # check headings are correct else throw exception

    n_created = 0
    n_updated = 0
    n_not_created_or_updated = 0
    for line in schools_list_reader:
        (name, subscription_paid_text, administrator_email) = (line['name'], line['subscription_paid'],
                                                               line['administrator_email'])
        subscription_paid = (subscription_paid_text == "Yes")
        if School.create_school_and_administrator(name=name, subscription_paid=subscription_paid,
                                                  administrator_email=administrator_email):
            n_created += 1
        elif School.update_school(name=name, subscription_paid=subscription_paid):
            n_updated += 1
        else:
            n_not_created_or_updated += 1

    return n_created, n_updated, n_not_created_or_updated


def add_test_categories_from_file_upload(uploaded_file):
    file_path_on_server = save_file(uploaded_file)
    (n_created, n_updated, n_not_created_or_updated) = add_test_categories_from_file(file_path_on_server)
    delete_file(file_path_on_server)
    return n_created, n_updated, n_not_created_or_updated


def add_test_categories_from_file(file_path_on_server):
    file_handle = open(file_path_on_server, 'rb')

    dialect = csv.Sniffer().sniff(file_handle.read(1024))
    dialect.strict = True

    file_handle.seek(0)
    test_categories_list_reader = csv.DictReader(file_handle, dialect=dialect)
    # check headings are correct else throw exception

    n_created = 0
    n_updated = 0
    n_not_created_or_updated = 0
    for line in test_categories_list_reader:
        (test_category_name) = (line['test_category_name'])
        if TestCategory.create_test_category(test_category_name=test_category_name):
            n_created += 1
        elif TestCategory.update_test_category(test_category_name=test_category_name):
            n_updated += 1
        else:
            n_not_created_or_updated += 1

    return n_created, n_updated, n_not_created_or_updated


def add_test_from_file_upload(uploaded_file):
    test_information = read_test_information_from_file_upload(uploaded_file)
    if test_information:
        (test_name, test_category, description, result_information) = test_information
        test = Test.create_test(test_name, test_category, description, result_information)
    else:
        test = None
    return test


def update_test_from_file_upload(uploaded_file, test):
    test_information = read_test_information_from_file_upload(uploaded_file)
    if test_information:
        (test_name, test_category, description, result_information) = test_information
        (result_type, is_upward_percentile_brackets,
         percentile_score_conversion_type, percentile_scores) = result_information
        if test.test_name == test_name:
            test = Test.update_test(test_name, description, percentile_scores)
        else:
            test = None
    else:
        test = None
    return test


def read_test_information_from_file_upload(uploaded_file):
    file_path_on_server = save_file(uploaded_file)
    test_information = read_test_information_from_file(file_path_on_server)
    delete_file(file_path_on_server)
    return test_information


def read_test_information_from_file(file_path_on_server):
    file_handle = open(file_path_on_server, 'rb')

    dialect = csv.Sniffer().sniff(file_handle.read(1024))
    dialect.strict = True

    file_handle.seek(0)
    test_reader = csv.reader(file_handle, dialect=dialect)

    test_name = ''
    test_category_name = ''
    description = ''
    result_type = ''
    is_upward_percentile_brackets = False
    percentile_score_conversion_type = ''
    for line_counter in range(6):
        line = test_reader.next()
        label = line[0]
        value = line[1]
        if label == 'test name':
            test_name = value
        elif label == 'test category name':
            test_category_name = value
        elif label == 'description':
            description = value
        elif label == 'result type':
            result_type = value
        elif label == 'is upward percentile brackets':
            is_upward_percentile_brackets = (value == 'Yes')
        elif label == 'percentile score conversion type':
            percentile_score_conversion_type = value

    values_ok = (
        (test_name != '') and TestCategory.objects.filter(test_category_name=test_category_name).exists() and
        (description != '') and
        (result_type in [res_type for (res_type, text) in PercentileBracketSet.RESULT_TYPE_CHOICES]) and
        (percentile_score_conversion_type in
         [con_type for (con_type, text) in PercentileBracketSet.PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES])
    )

    if values_ok:
        test_category = TestCategory.objects.get(test_category_name=test_category_name)
        line = test_reader.next()
        n_percentiles = len(line)
        percentiles = []
        for percentile_text in line[2:n_percentiles]:
            percentiles.append(int(percentile_text))
        age_genders = []
        score_table = []
        for line in test_reader:
            age_genders.append((int(line[0]), line[1]))
            score_table.append(line[2:n_percentiles])
        percentile_scores = (percentiles, age_genders, score_table)
        result_information = (result_type, is_upward_percentile_brackets,
                              percentile_score_conversion_type, percentile_scores)
        test_information = (test_name, test_category, description, result_information)
    else:
        test_information = None

    return test_information