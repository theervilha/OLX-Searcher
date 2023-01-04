from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('send_message', views.send_message, name='send_message'),
    path('handle_message', views.handle_message, name='handle_message'),
    path('search/get_links_per_user', views.get_links_per_user, name='get_links_per_user'),
    path('search/update_last_time_runned_link', views.update_last_time_runned_link, name='update_last_time_runned_link'),
    path('search/insert_search', views.insert_search, name='insert_search'),
    path('search/delete_search', views.delete_search, name='delete_search'),
]
