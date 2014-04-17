import csv
import tempfile
from fitness_scoring.models import Student, Teacher, Class, School, User, TestCategory, Test
import os

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
        (student_id, first_name, surname, gender, dob) = (line['student_id'], line['first_name'], line['surname'], line['gender'], line['dob'])
        if Student.create_student(check_name=False, student_id=student_id, school_id=school_id, first_name=first_name, surname=surname, gender=gender, dob=dob):
            n_created += 1
        elif Student.update_student(check_name=False,student_id=student_id, school_id=school_id, first_name=first_name, surname=surname, gender=gender, dob=dob):
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
        (first_name, surname, username, password) = (line['first_name'], line['surname'], line['username'], line['password'])
        if Teacher.create_teacher(check_name=False, first_name=first_name, surname=surname, school_id=school_id, username=username, password=password):
            n_created += 1
        elif Teacher.update_teacher(check_name=False, first_name=first_name, surname=surname, school_id=school_id, username=username, password=password):
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
        teacher_id = Teacher.objects.get(user=User.objects.get(username=teacher_username))\
            if (len(User.objects.filter(username=teacher_username)) == 1) and\
               (len(Teacher.objects.filter(user=User.objects.get(username=teacher_username), school_id=school_id)) == 1)\
            else None

        if Class.create_class(year=year, class_name=class_name, school_id=school_id, teacher_id=teacher_id):
            n_created += 1
        elif Class.update_class(year=year, class_name=class_name, school_id=school_id, teacher_id=teacher_id):
            n_updated += 1
        else:
            n_not_created_or_updated += 1

    return n_created, n_updated, n_not_created_or_updated


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
        (name, subscription_paid_text) = (line['name'], line['subscription_paid'])
        subscription_paid = (subscription_paid_text == "Yes")
        if School.create_school_and_administrator(name=name, subscription_paid=subscription_paid):
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


def add_tests_from_file_upload(uploaded_file):
    file_path_on_server = save_file(uploaded_file)
    (n_created, n_updated, n_not_created_or_updated) = add_tests_from_file(file_path_on_server)
    delete_file(file_path_on_server)
    return n_created, n_updated, n_not_created_or_updated


def add_tests_from_file(file_path_on_server):
    file_handle = open(file_path_on_server, 'rb')

    dialect = csv.Sniffer().sniff(file_handle.read(1024))
    dialect.strict = True

    file_handle.seek(0)
    test_list_reader = csv.DictReader(file_handle, dialect=dialect)
    # check headings are correct else throw exception

    n_created = 0
    n_updated = 0
    n_not_created_or_updated = 0
    for line in test_list_reader:

        (test_name, test_category_name, description, result_type,
         is_upward_percentile_brackets, percentile_score_conversion_type) =\
            (line['test_name'], line['test_category_name'], line['description'], line['result_type'],
             (line['is_upward_percentile_brackets'] == 'Yes'), line['percentile_score_conversion_type'])

        try:
            test_category = TestCategory.objects.get(test_category_name=test_category_name)

            if Test.create_test(test_name=test_name, test_category=test_category, description=description,
                                result_type=result_type, is_upward_percentile_brackets=is_upward_percentile_brackets,
                                percentile_score_conversion_type=percentile_score_conversion_type):
                n_created += 1
            elif Test.update_test(test_name=test_name, test_category=test_category, description=description,
                                  result_type=result_type, is_upward_percentile_brackets=is_upward_percentile_brackets,
                                  percentile_score_conversion_type=percentile_score_conversion_type):
                n_updated += 1
            else:
                n_not_created_or_updated += 1
        except Exception:
            n_not_created_or_updated += 1

    return n_created, n_updated, n_not_created_or_updated