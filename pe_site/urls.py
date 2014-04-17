
from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '', url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'fitness_scoring.views.login_user'),
    url(r'^login', 'fitness_scoring.views.login_user', name='login'),
    url(r'^logout/', 'fitness_scoring.views.logout_user', name='logout'),
    url(r'^teacher/', 'fitness_scoring.views.teacher_view', name='teacher'),
    url(r'^administrator/$', 'fitness_scoring.views.administrator_view', name='administrator'),
    url(r'^superuser/', 'fitness_scoring.views.superuser_view', name='superuser'),
    url(r'^superuser_home/', 'fitness_scoring.views.superuser_home', name='superuser_home'),
    url(r'^school/list/', 'fitness_scoring.views.school_list', name='school_list'),
    url(r'^school/add/', 'fitness_scoring.views.school_add', name='school_add'),
    url(r'^school/adds/', 'fitness_scoring.views.school_adds', name='school_adds'),
    url(r'^school/edit/(?P<school_pk>\d+)', 'fitness_scoring.views.school_edit', name='school_edit'),
    url(r'^school/delete/(?P<school_pk>\d+)', 'fitness_scoring.views.school_delete', name='school_delete'),
    url(r'^test_category/list/', 'fitness_scoring.views.test_category_list', name='test_category_list'),
    url(r'^test_category/add/', 'fitness_scoring.views.test_category_add', name='test_category_add'),
    url(r'^test_category/adds/', 'fitness_scoring.views.test_category_adds', name='test_category_adds'),
    url(r'^test_category/edit/(?P<test_category_pk>\d+)', 'fitness_scoring.views.test_category_edit',
        name='test_category_edit'),
    url(r'^test_category/delete/(?P<test_category_pk>\d+)', 'fitness_scoring.views.test_category_delete',
        name='test_category_delete'),
    url(r'^test/list/', 'fitness_scoring.views.test_list', name='test_list'),
    url(r'^test/add/', 'fitness_scoring.views.test_add', name='test_add'),
    url(r'^test/adds/', 'fitness_scoring.views.test_adds', name='test_adds'),
    url(r'^test/edit/(?P<test_pk>\d+)', 'fitness_scoring.views.test_edit', name='test_edit'),
    url(r'^test/delete/(?P<test_pk>\d+)', 'fitness_scoring.views.test_delete', name='test_delete'),
)
