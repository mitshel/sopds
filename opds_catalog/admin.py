from django.contrib import admin
from opds_catalog.models import Genre

# Register your models here.
class Genre_admin(admin.ModelAdmin):
    list_display = ('genre', 'section', 'subsection')

admin.site.register(Genre, Genre_admin)
