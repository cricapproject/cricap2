from django.contrib import admin

from .models import Question, Response, SubQuestion, Section, DataDiri, IRKResult

# Register your models here.

# from .models import Profile

admin.site.register(Question)
admin.site.register(Response)
admin.site.register(SubQuestion)
admin.site.register(Section)
admin.site.register(DataDiri)
admin.site.register(IRKResult)
