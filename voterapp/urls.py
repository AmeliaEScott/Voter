from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^vote/$', views.vote, name='vote'),
    url(r'^faq/$', views.faq, name='faq'),
    url(r'^submitvote/$', views.submitvote, name='submitvote'),
    url(r'^confirmvote/(?P<voteid>[a-zA-z0-9+_]{32})/$', views.confirmvote, name='confirmvote')
]
