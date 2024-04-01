from django.contrib import admin

from .models import QuestionType, Category, SupportObjective, Question

admin.site.register(QuestionType)
admin.site.register(Category)
admin.site.register(SupportObjective)
admin.site.register(Question)
