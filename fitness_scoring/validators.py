
from fitness_scoring.models import School
from django.core.exceptions import ValidationError


def validate_school_unique(name):
    if School.objects.filter(name=name).exists():
        raise ValidationError('School Already Exists: ' + name)
