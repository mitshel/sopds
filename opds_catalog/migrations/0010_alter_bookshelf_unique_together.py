# Generated by Django 4.1.1 on 2022-09-19 07:09

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('opds_catalog', '0009_alter_author_id_alter_bauthor_id_alter_bgenre_id_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='bookshelf',
            unique_together={('user', 'book')},
        ),
    ]