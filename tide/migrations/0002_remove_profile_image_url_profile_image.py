# Generated by Django 5.1.2 on 2024-11-02 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tide', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='image_url',
        ),
        migrations.AddField(
            model_name='profile',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='profile_images/'),
        ),
    ]