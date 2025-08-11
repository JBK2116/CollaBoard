from django.contrib import admin

from apps.base.models import CustomUser, PasswordResetToken

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(PasswordResetToken)
