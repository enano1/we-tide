# Generated by Django 5.1.2 on 2024-11-14 19:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tide', '0015_remove_comment_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='statusmessage',
            name='likes_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]