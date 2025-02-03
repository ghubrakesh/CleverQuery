from django.contrib import admin

from .models import Document, Query, Session

# Register your models here.
admin.site.register(Session)
admin.site.register(Document)
admin.site.register(Query)
