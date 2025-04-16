from django.urls import path
from ..views import admin_views

admin_urlpatterns = [
    path('dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('approve/<int:user_id>/', admin_views.admin_approve_user, name='admin_approve_user'),
    path('create-batch/', admin_views.admin_create_batch, name='admin_create_batch'),
    path('create-batch-auto/', admin_views.admin_create_batch_auto, name='admin_create_batch_auto'),
    path('delete-batch/<int:batch_id>/', admin_views.admin_delete_batch, name='admin_delete_batch'),
    path('batch/<int:batch_id>/', admin_views.batch_details, name='batch_details'),
]