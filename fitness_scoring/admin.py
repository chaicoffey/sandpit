from django.contrib import admin
from fitness_scoring.models import School, Teacher, Administrator, Student, Class, Test, DefaultTest
from fitness_scoring.models import TeacherClassAllocation, StudentClassEnrolment, ClassTest, StudentClassTestResult
from fitness_scoring.models import PercentileBracketSet, PercentileBracketList, TestCategory, SuperUser, User
from fitness_scoring.models import StudentsSameID, StudentsSameName


class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'subscription_paid')
    list_editable = ('subscription_paid',)


class TeacherClassAllocationAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'class_id')

# Register your models here.

admin.site.register(School, SchoolAdmin)
admin.site.register(Teacher)
admin.site.register(Administrator)
admin.site.register(User)
admin.site.register(SuperUser)
admin.site.register(Student)
admin.site.register(Class)
admin.site.register(Test)
admin.site.register(DefaultTest)
admin.site.register(TeacherClassAllocation, TeacherClassAllocationAdmin)
admin.site.register(StudentClassEnrolment)
admin.site.register(ClassTest)
admin.site.register(StudentClassTestResult)
admin.site.register(PercentileBracketSet)
admin.site.register(PercentileBracketList)
admin.site.register(TestCategory)
admin.site.register(StudentsSameID)
admin.site.register(StudentsSameName)