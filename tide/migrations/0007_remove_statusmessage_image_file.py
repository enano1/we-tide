# Generated by Django 5.1.2 on 2024-11-03 21:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tide', '0006_statusmessage_image_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='statusmessage',
            name='image_file',
        ),
    ]
