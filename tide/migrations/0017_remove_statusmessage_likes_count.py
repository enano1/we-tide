# Generated by Django 5.1.2 on 2024-11-14 19:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tide', '0016_statusmessage_likes_count'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='statusmessage',
            name='likes_count',
        ),
    ]
