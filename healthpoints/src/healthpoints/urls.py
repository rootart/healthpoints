from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic import TemplateView

admin.autodiscover()

from tracks.views import MainView, ShareFBView, ShareEvernoteView, LogoutView, DemoProfileView

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url('^$', MainView.as_view(), name='main'),
    url('^demo/$', DemoProfileView.as_view(), name='demo'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url(r'share/fb/$', ShareFBView.as_view(), name='share-fb'),
    url(r'share/evernote/$', ShareEvernoteView.as_view(), name='share-evernote'),
    url('', include('social.apps.django_app.urls', namespace='social')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
        }),
    )
    urlpatterns += patterns('',
        url(r'^error-page/404/$', TemplateView.as_view(template_name='404.html')),
        url(r'^error-page/500/$', TemplateView.as_view(template_name='500.html'))
    )


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
