from django.test import TestCase
from fitness_scoring.models import School, Teacher

# Create your tests here.


class SchoolMethodTests(TestCase):

    def test_delete_school_safe_with_assigned_teachers(self):
        """
        delete_school_safe() should return False for schools who have teachers
        assigned to them.
        """
        testschool = School(name="Test School")
        testschool_teacher = Teacher(first_name='F1', surname='S1', school_id=testschool)
        self.assertEqual(testschool.delete_school_safe(), False)