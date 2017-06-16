from django.conf.urls import url

from . import views

app_name = 'minesweeper'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^new_game/$', views.new_game, name='new_game'),
    url(r'^restore/$', views.restore, name='restore'),
    url(r'^reveal/$', views.reveal, name='reveal'),
    url(r'^toggle_flag/$', views.toggle_flag, name='toggle_flag'),
]
