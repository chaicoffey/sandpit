import csv
import tempfile
from fitness_scoring.models import Student

destination_directory = '/tmp/fitness_scoring/'


def save_file(f):
    destination_file = tempfile.NamedTemporaryFile(dir=destination_directory, delete=False)
    destination_file.seek(0)
    for chunk in f.chunks():
        destination_file.write(chunk)
    destination_file.flush()
    destination_file.close()
    return destination_file.name


def add_students_from_file(file_path_on_server, school_id):
    file_handle = open(file_path_on_server, 'rb')

    dialect = csv.Sniffer().sniff(file_handle.read(1024))
    dialect.strict = True

    file_handle.seek(0)
    students_list_reader = csv.DictReader(file_handle, dialect=dialect)
    # check headings are correct else throw exception
    for line in students_list_reader:
        # do some checks on here on same student etc
        Student.objects.create(student_id=line['student_id'], school_id=school_id, firstname=line['firstname'], surname=line['surname'], gender=line['gender'], dob=line['dob'])

    file_handle.close()
    #for each record
    #   check if studentID exists, check name same and dob, if same overwrite other details if not don't add
    #   if same name and school but different ID then give warning promt and ask if want to do
    #   if any problem with data dont add
    #   keep list of all rows added and all rows not added and all rows overwritten
    #   add record to database
    #Return summary at end, n added, n updated, n not added, rows with same name but different ID

