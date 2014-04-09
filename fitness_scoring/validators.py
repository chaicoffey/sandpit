
from fitness_scoring.models import School
from django.core.exceptions import ValidationError


def validate_school_unique(name):
    if School.objects.filter(name=name).exists():
        raise ValidationError('School Already Exists: ' + name)


def validate_no_space(n_characters):

    def space_test(value):
        if ' ' in value[0:(n_characters)]:
            raise ValidationError('Spaces Found', code='no_space')

    return space_test