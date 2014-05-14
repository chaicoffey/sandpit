
from fitness_scoring.models import School, TestCategory, Test, Student
from pe_site.settings import MAX_FILE_UPLOAD_SIZE_MB
from django.core.exceptions import ValidationError
import datetime


def validate_file_size(file_data):
    if file_data:
        if file_data._size > (1024*1024*MAX_FILE_UPLOAD_SIZE_MB):
            raise ValidationError("File too large (must be less than: " + str(MAX_FILE_UPLOAD_SIZE_MB) + " MB)")
        return file_data
    else:
        raise ValidationError("Couldn't read uploaded file")


def validate_test_category_unique(test_category_name):
    if TestCategory.objects.filter(test_category_name=test_category_name).exists():
        raise ValidationError('Test Category Already Exists: ' + test_category_name)


def validate_new_test_category_name_unique(test_category_pk):

    def new_test_category_name_unique(test_category_name):
        test_category = TestCategory.objects.get(pk=test_category_pk)
        if (test_category.test_category_name != test_category_name) and\
                (TestCategory.objects.filter(test_category_name=test_category_name).exists()):
            raise ValidationError('Test Category Name Already Exists: ' + test_category_name)

    return new_test_category_name_unique


def validate_new_test_name_unique(test_pk):

    def new_test_name_unique(test_name):
        test = Test.objects.get(pk=test_pk)
        if (test.test_name != test_name) and\
                (Test.objects.filter(test_name=test_name).exists()):
            raise ValidationError('Test Category Name Already Exists: ' + test_name)

    return new_test_name_unique


def validate_student_unique(school_pk):

    def student_unique(student_id):
        school = School.objects.get(pk=school_pk)
        if Student.objects.filter(student_id=student_id, school_id=school).exists():
            raise ValidationError('Student ID Already Exists: ' + student_id)

    return student_unique


def validate_new_student_id_unique(student_pk, school_pk):

    def new_student_id_unique(student_id):
        student = Student.objects.get(pk=student_pk)
        school = School.objects.get(pk=school_pk)
        if (student.student_id != student_id) and (Student.objects.filter(student_id=student_id,
                                                                          school_id=school).exists()):
            raise ValidationError('Student ID Already Exists: ' + student_id)

    return new_student_id_unique


def validate_no_space(n_characters):

    def space_test(value):
        if ' ' in value[0:n_characters]:
            raise ValidationError('Spaces Found', code='no_space')

    return space_test


def validate_date_field(date_format):

    def test_date_field(date_text):
        try:
            datetime.datetime.strptime(date_text, date_format)
        except ValueError:
            raise ValidationError("Date should be of form " + date_format, code='date_format')

    return test_date_field