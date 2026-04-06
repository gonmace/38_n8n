from django.urls import path

from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.conversation_list, name='list'),
    path('new/', views.new_conversation, name='new'),
    path('<int:pk>/', views.chat_detail, name='detail'),
    path('<int:pk>/send/', views.send_message, name='send'),
    path('settings/', views.user_settings, name='settings'),
    path('facts/add/', views.add_fact, name='fact_add'),
    path('facts/<int:pk>/delete/', views.delete_fact, name='fact_delete'),
]
