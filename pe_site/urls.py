
from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'fitness_scoring.views.login_user'),
    url(r'^login', 'fitness_scoring.views.login_user', name='login'),
    url(r'^logout/', 'fitness_scoring.views.logout_user'),
    url(r'^teacher/', 'fitness_scoring.views.teacher'),
    url(r'^administrator/$', 'fitness_scoring.views.administrator', name='administrator'),
    url(r'^superuser/', 'fitness_scoring.views.superuser'),
    url(r'^school/list/', 'fitness_scoring.views.school_list', name='school_list'),
    url(r'^school/add/', 'fitness_scoring.views.school_add', name='school_add'),
    url(r'^school/adds/', 'fitness_scoring.views.school_adds', name='school_adds'),
    url(r'^school/edit/(?P<school_pk>\d+)', 'fitness_scoring.views.school_edit', name='school_edit'),
    url(r'^school/delete/(?P<school_pk>\d+)', 'fitness_scoring.views.school_delete', name='school_delete'),
)
