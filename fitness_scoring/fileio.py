import csv
import tempfile
import os
from pe_site.settings import BASE_DIR
from fitness_scoring.models import MajorTestCategory, TestCategory
from fitness_scoring.models import PercentileBracketSet


destination_directory = os.path.join(BASE_DIR, 'file_uploads')


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


def read_file_upload(uploaded_file, headings):
    file_path_on_server = save_file(uploaded_file)
    try:
        result = read_file(file_path_on_server, headings)
    except:
        result = None
    delete_file(file_path_on_server)
    return result


def read_file(file_path_on_server, headings):
    file_handle = open(file_path_on_server, 'rb')

    try:
        dialect = csv.Sniffer().sniff(file_handle.read(1024))
        dialect.strict = True

        file_handle.seek(0)
        classes_list_reader = csv.DictReader(file_handle, dialect=dialect)
        # check headings are correct else throw exception

        valid_lines = []
        invalid_lines = []
        for line in classes_list_reader:
            try:
                data_line = []
                for heading in headings:
                    data_line.append(line[heading])
                valid_lines.append(data_line)
            except:
                invalid_lines.append(line)
    finally:
        file_handle.close()

    return valid_lines, invalid_lines


def read_test_information_from_file_upload(uploaded_file):
    file_path_on_server = save_file(uploaded_file)
    try:
        result = read_test_information_from_file(file_path_on_server)
    except:
        result = None
    delete_file(file_path_on_server)
    return result


def read_test_information_from_file(file_path_on_server):
    file_handle = open(file_path_on_server, 'rb')

    try:
        dialect = csv.Sniffer().sniff(file_handle.read(1024))
        dialect.strict = True

        file_handle.seek(0)
        test_reader = csv.reader(file_handle, dialect=dialect)

        problems_in_data = []

        test_name = ''
        test_category_name = ''
        major_test_category_name = ''
        result_type = ''
        result_unit = ''
        is_upward_percentile_brackets = False
        percentile_score_conversion_type = ''
        for line_counter in range(7):
            try:
                line = test_reader.next()
                label = line[0]
                value = line[1]
                if label == 'test name':
                    test_name = value
                elif label == 'test category name':
                    test_category_name = value
                elif label == 'major test category name':
                    major_test_category_name = value
                elif label == 'result type':
                    result_type = value
                elif label == 'result unit':
                    result_unit = value
                elif label == 'is upward percentile brackets':
                    is_upward_percentile_brackets = (value == 'Yes')
                elif label == 'percentile score conversion type':
                    percentile_score_conversion_type = value
            except:
                problems_in_data.append('error reading line ' + str(line_counter + 1))

        if test_name == '':
            problems_in_data.append('test name missing')
        if not TestCategory.objects.filter(test_category_name=test_category_name).exists():
            problems_in_data.append('test category name missing or not recognised')
        if not MajorTestCategory.objects.filter(major_test_category_name=major_test_category_name).exists():
            problems_in_data.append('major test category name missing or not recognised')
        if result_type not in [res_type for (res_type, text) in PercentileBracketSet.RESULT_TYPE_CHOICES]:
            problems_in_data.append('result type missing or not recognised')
        if result_unit == '':
            problems_in_data.append('result unit missing')
        if percentile_score_conversion_type not in [con_type for (con_type, text) in
                                                    PercentileBracketSet.PERCENTILE_SCORE_CONVERSION_TYPE_CHOICES]:
            problems_in_data.append('percentile score conversion type missing or not recognised')

        if len(problems_in_data) == 0:
            test_category = TestCategory.objects.get(test_category_name=test_category_name)
            major_test_category = MajorTestCategory.objects.get(major_test_category_name=major_test_category_name)
            try:
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
                result_information = (result_type, result_unit, is_upward_percentile_brackets,
                                      percentile_score_conversion_type, percentile_scores)
                test_information = (test_name, test_category, major_test_category, result_information)
            except:
                problems_in_data.append('problem reading percentile data')
                test_information = None
        else:
            test_information = None
    finally:
        file_handle.close()

    return problems_in_data, test_information