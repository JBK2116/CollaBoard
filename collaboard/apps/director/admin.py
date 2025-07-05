from django.contrib import admin

from apps.director.models import Meeting, Question, Response

# Register your models here.
admin.site.register(Meeting)
admin.site.register(Question)
admin.site.register(Response)
