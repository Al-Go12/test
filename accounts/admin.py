# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, OTP


# Custom forms for the User model
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('phone_number',)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            'phone_number',
            'is_phone_verified',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        )


# Custom UserAdmin
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = [
        'phone_number',
        'is_phone_verified',
        'is_active',
        'is_staff',
        'is_superuser',
        'last_login',
    ]
    list_filter = ['is_phone_verified', 'is_active', 'is_staff', 'is_superuser']

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'is_phone_verified',
                'groups',
                'user_permissions',
            ),
        }),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2'),
        }),
    )

    search_fields = ['phone_number']
    ordering = ['-id']  # since date_joined doesn't exist anymore


# OTP Admin
class OTPAdmin(admin.ModelAdmin):
    list_display = ['mobile', 'code', 'created_at', 'is_verified', 'is_expired_status']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['mobile', 'code']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def is_expired_status(self, obj):
        return obj.is_expired()
    is_expired_status.boolean = True
    is_expired_status.short_description = 'Expired'


# Register the models
admin.site.register(User, CustomUserAdmin)
admin.site.register(OTP, OTPAdmin)
