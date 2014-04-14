
from fitness_scoring.models import School, TestCategory
from django.core.exceptions import ValidationError


def validate_school_unique(name):
    if School.objects.filter(name=name).exists():
        raise ValidationError('School Already Exists: ' + name)


def validate_test_category_unique(test_category_name):
    if TestCategory.objects.filter(test_category_name=test_category_name).exists():
        raise ValidationError('Test Category Already Exists: ' + test_category_name)


def validate_no_space(n_characters):

    def space_test(value):
        if ' ' in value[0:n_characters]:
            raise ValidationError('Spaces Found', code='no_space')

    return space_test