
from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '', url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'fitness_scoring.views.login_user'),
    url(r'^login', 'fitness_scoring.views.login_user', name='login'),
    url(r'^licencing_check', 'fitness_scoring.views.licencing_check', name='licencing_check'),
    url(r'^logout/', 'fitness_scoring.views.logout_user', name='logout'),
    url(r'^change_password/(?P<is_finished>\w+)', 'fitness_scoring.views.change_user_password',
        name='change_user_password'),
    url(r'^superuser_view/', 'fitness_scoring.views.superuser_view', name='superuser_view'),
    url(r'^superuser_home/', 'fitness_scoring.views.superuser_home', name='superuser_home'),
    url(r'^administrator_view/', 'fitness_scoring.views.administrator_view', name='administrator_view'),
    url(r'^administrator_home/', 'fitness_scoring.views.administrator_home', name='administrator_home'),
    url(r'^teacher_view/', 'fitness_scoring.views.teacher_view', name='teacher_view'),
    url(r'^teacher_home/', 'fitness_scoring.views.teacher_home', name='teacher_home'),
    url(r'^class_student_view/', 'fitness_scoring.views.class_student_view', name='class_student_view'),
    url(r'^class_student_results_view/(?P<enrolment_pk>\d+)', 'fitness_scoring.views.class_student_results_view',
        name='class_student_results_view'),
    url(r'^school/list/', 'fitness_scoring.views.school_list', name='school_list'),
    url(r'^instructions_page/(?P<instructions_name>\w+)', 'fitness_scoring.views.instructions_page',
        name='instructions_page'),
    url(r'^school/add/', 'fitness_scoring.views.school_add', name='school_add'),
    url(r'^school/adds/', 'fitness_scoring.views.school_adds', name='school_adds'),
    url(r'^school/edit/(?P<school_pk>\d+)', 'fitness_scoring.views.school_edit', name='school_edit'),
    url(r'^school/delete/(?P<school_pk>\d+)', 'fitness_scoring.views.school_delete', name='school_delete'),
    url(r'^school/reset_password/(?P<school_pk>\d+)', 'fitness_scoring.views.school_reset_password',
        name='school_reset_password'),
    url(r'^test_category/list/', 'fitness_scoring.views.test_category_list', name='test_category_list'),
    url(r'^test_category/add/', 'fitness_scoring.views.test_category_add', name='test_category_add'),
    url(r'^test_category/adds/', 'fitness_scoring.views.test_category_adds', name='test_category_adds'),
    url(r'^test_category/edit/(?P<test_category_pk>\d+)', 'fitness_scoring.views.test_category_edit',
        name='test_category_edit'),
    url(r'^test_category/delete/(?P<test_category_pk>\d+)', 'fitness_scoring.views.test_category_delete',
        name='test_category_delete'),
    url(r'^major_test_category/list/', 'fitness_scoring.views.major_test_category_list',
        name='major_test_category_list'),
    url(r'^major_test_category/add/', 'fitness_scoring.views.major_test_category_add', name='major_test_category_add'),
    url(r'^major_test_category/adds/', 'fitness_scoring.views.major_test_category_adds',
        name='major_test_category_adds'),
    url(r'^major_test_category/edit/(?P<major_test_category_pk>\d+)', 'fitness_scoring.views.major_test_category_edit',
        name='major_test_category_edit'),
    url(r'^major_test_category/delete/(?P<major_test_category_pk>\d+)',
        'fitness_scoring.views.major_test_category_delete', name='major_test_category_delete'),
    url(r'^test/list/', 'fitness_scoring.views.test_list', name='test_list'),
    url(r'^test/adds/', 'fitness_scoring.views.test_adds', name='test_adds'),
    url(r'^test/edit/(?P<test_pk>\d+)', 'fitness_scoring.views.test_edit', name='test_edit'),
    url(r'^test/update/(?P<test_pk>\d+)', 'fitness_scoring.views.test_update', name='test_update'),
    url(r'^test/delete/(?P<test_pk>\d+)', 'fitness_scoring.views.test_delete', name='test_delete'),
    url(r'^test/percentile_brackets_graphs/(?P<percentile_bracket_list_pk>\w+)/(?P<test_pk>\d+)',
        'fitness_scoring.views.test_percentile_brackets_graphs', name='test_percentile_brackets_graphs'),
    url(r'^test/instructions/(?P<test_pk>\d+)', 'fitness_scoring.views.test_instructions', name='test_instructions'),
    url(r'^teacher/list/', 'fitness_scoring.views.teacher_list', name='teacher_list'),
    url(r'^teacher/add/', 'fitness_scoring.views.teacher_add', name='teacher_add'),
    url(r'^teacher/edit/(?P<teacher_pk>\d+)', 'fitness_scoring.views.teacher_edit', name='teacher_edit'),
    url(r'^teacher/delete/(?P<teacher_pk>\d+)', 'fitness_scoring.views.teacher_delete', name='teacher_delete'),
    url(r'^teacher/reset_password/(?P<teacher_pk>\d+)', 'fitness_scoring.views.teacher_reset_password',
        name='teacher_reset_password'),
    url(r'^class/list/', 'fitness_scoring.views.class_list', name='class_list'),
    url(r'^class/add/', 'fitness_scoring.views.class_add', name='class_add'),
    url(r'^class/adds/', 'fitness_scoring.views.class_adds', name='class_adds'),
    url(r'^class/edit/(?P<class_pk>\d+)', 'fitness_scoring.views.class_edit', name='class_edit'),
    url(r'^class/delete/(?P<class_pk>\d+)', 'fitness_scoring.views.class_delete', name='class_delete'),
    url(r'^class/class/(?P<class_pk>\d+)', 'fitness_scoring.views.class_class', name='class_class'),
    url(r'^class/results_table/(?P<class_pk>\d+)', 'fitness_scoring.views.class_results_table',
        name='class_results_table'),
    url(r'^class/results_graphs/tests/(?P<class_pk>\d+)/$', 'fitness_scoring.views.class_results_graphs_tests'),
    url(r'^class/results_graphs/tests/(?P<class_pk>\d+)/(?P<test_pk>\d+)/$',
        'fitness_scoring.views.class_results_graphs_tests'),
    url(r'^class/results_graphs/students/(?P<class_pk>\d+)/$', 'fitness_scoring.views.class_results_graphs_students'),
    url(r'^class/results_graphs/students/(?P<class_pk>\d+)/(?P<student_pk>\d+)/$',
        'fitness_scoring.views.class_results_graphs_students'),
    url(r'^class/results_graphs/previous/(?P<class_pk>\d+)/$', 'fitness_scoring.views.class_results_graphs_previous'),
    url(r'^class/results_graphs/previous/(?P<class_pk>\d+)/(?P<student_pk>\d+)/$',
        'fitness_scoring.views.class_results_graphs_previous'),
    url(r'^class/results_graphs/previous/(?P<class_pk>\d+)/(?P<student_pk>\d+)/(?P<test_pk>\d+)/$',
        'fitness_scoring.views.class_results_graphs_previous'),
    url(r'^class/test/add/(?P<class_pk>\d+)', 'fitness_scoring.views.add_test_to_class', name='add_test_to_class'),
    url(r'^class/test_set/save/(?P<class_pk>\d+)', 'fitness_scoring.views.save_class_tests_as_test_set',
        name='save_class_tests_as_test_set'),
    url(r'^class/test_set/load/(?P<class_pk>\d+)', 'fitness_scoring.views.load_class_tests_from_test_set',
        name='load_class_tests_from_test_set'),
    url(r'^class/get_new_code/(?P<class_pk>\d+)', 'fitness_scoring.views.get_new_class_code',
        name='get_new_class_code'),
    url(r'^class/approve_all/(?P<class_pk>\d+)', 'fitness_scoring.views.approve_all_class_results',
        name='approve_all_class_results'),
    url(r'^class/test/delete/(?P<class_pk>\d+)/(?P<test_pk>\d+)', 'fitness_scoring.views.remove_test_from_class',
        name='remove_test_from_class'),
    url(r'^class_enrolment/approve/(?P<enrolment_pk>\d+)', 'fitness_scoring.views.class_enrolment_approve',
        name='class_enrolment_approve'),
    url(r'^class_enrolment/un_approve/(?P<enrolment_pk>\d+)', 'fitness_scoring.views.class_enrolment_un_approve',
        name='class_enrolment_un_approve'),
    url(r'^class_enrolment/resolve_pending_issues/(?P<enrolment_pk>\d+)',
        'fitness_scoring.views.class_enrolment_resolve_pending_issues', name='class_enrolment_resolve_pending_issues'),
    url(r'^class_enrolment/edit/(?P<enrolment_pk>\d+)', 'fitness_scoring.views.class_enrolment_edit',
        name='class_enrolment_edit'),
    url(r'^class_enrolment/delete/(?P<enrolment_pk>\d+)', 'fitness_scoring.views.class_enrolment_delete',
        name='class_enrolment_delete'),
)
