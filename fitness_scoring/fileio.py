import csv
import tempfile
from fitness_scoring.models import create_student, update_student

destination_directory = 'C:\\fitness_scoring_file_uploads\\'


def save_file(f):
    destination_file = tempfile.NamedTemporaryFile(dir=destination_directory, delete=False)
    destination_file.seek(0)
    for chunk in f.chunks():
        destination_file.write(chunk)
    destination_file.flush()
    destination_file.close()
    return destination_file.name

def delete_file(file_name):
    pass

def add_students_from_file(file_path_on_server, school_id):
    file_handle = open(file_path_on_server, 'rb')

    dialect = csv.Sniffer().sniff(file_handle.read(1024))
    dialect.strict = True

    file_handle.seek(0)
    students_list_reader = csv.DictReader(file_handle, dialect=dialect)
    # check headings are correct else throw exception
    for line in students_list_reader:
        (student_id, firstname, surname, gender, dob) = (line['student_id'], line['firstname'], line['surname'], line['gender'], line['dob'])
        if(not create_student(check_name=False, student_id=student_id, school_id=school_id, firstname=firstname, surname=surname, gender=gender, dob=dob)):
            update_student(check_name=False,student_id=student_id, school_id=school_id, firstname=firstname, surname=surname, gender=gender, dob=dob)

    #file_handle.close()
