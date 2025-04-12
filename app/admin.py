from django.contrib import admin
from .models import UserRegistration, Batch, BatchAssignment

@admin.action(description='Aprovar usuários selecionados')
def approve_users(modeladmin, request, queryset):
    for user in queryset:
        user.approve()

@admin.action(description='Rejeitar usuários selecionados')
def reject_users(modeladmin, request, queryset):
    for user in queryset:
        user.reject()

class UserRegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'status', 'created_at')
    actions = [approve_users, reject_users]

admin.site.register(UserRegistration, UserRegistrationAdmin)
admin.site.register(Batch)
admin.site.register(BatchAssignment)
