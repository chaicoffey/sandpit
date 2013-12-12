from django.contrib import admin
from fitness_scoring.models import School, Teacher, Administrator, Student, Class, Test, TeacherClassAllocation, StudentClassEnrolment, ClassTestSet, StudentClassTestResult, PercentileBracket, TestCategory, SuperUser, User
# Register your models here.

admin.site.register(School)
admin.site.register(Teacher)
admin.site.register(Administrator)
admin.site.register(User)
admin.site.register(SuperUser)
admin.site.register(Student)
admin.site.register(Class)
admin.site.register(Test)
admin.site.register(TeacherClassAllocation)
admin.site.register(StudentClassEnrolment)
admin.site.register(ClassTestSet)
admin.site.register(StudentClassTestResult)
admin.site.register(PercentileBracket)
admin.site.register(TestCategory)

