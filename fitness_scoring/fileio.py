import csv
import tempfile
from fitness_scoring.models import create_student, update_student, create_teacher, update_teacher, create_school_and_administrator, update_school
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
        if create_student(check_name=False, student_id=student_id, school_id=school_id, first_name=first_name, surname=surname, gender=gender, dob=dob):
            n_created += 1
        else:
            if update_student(check_name=False,student_id=student_id, school_id=school_id, first_name=first_name, surname=surname, gender=gender, dob=dob):
                n_updated += 1
            else:
                n_not_created_or_updated += 1

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
        if create_teacher(check_name=False, first_name=first_name, surname=surname, school_id=school_id, username=username, password=password):
            n_created += 1
        else:
            if update_teacher(check_name=False, first_name=first_name, surname=surname, school_id=school_id, username=username, password=password):
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
        if create_school_and_administrator(name=name, subscription_paid=subscription_paid):
            n_created += 1
        else:
            if update_school(name=name, subscription_paid=subscription_paid):
                n_updated += 1
            else:
                n_not_created_or_updated += 1

    return n_created, n_updated, n_not_created_or_updated