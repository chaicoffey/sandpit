from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'pe_site.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/', 'fitness_scoring.views.login_user'),
    url(r'^logout/', 'fitness_scoring.views.logout_user'),
    url(r'^teacher/', 'fitness_scoring.views.teacher'),
    url(r'^administrator/', 'fitness_scoring.views.administrator'),
    url(r'^superuser/', 'fitness_scoring.views.superuser'),
)
