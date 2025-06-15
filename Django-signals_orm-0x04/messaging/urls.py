from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('delete-account/', views.delete_user, name='delete_user'),
    path('delete-account-page/', views.delete_account_page, name='delete_account_page'),
]
