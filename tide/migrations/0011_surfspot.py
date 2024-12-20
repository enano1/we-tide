# Generated by Django 5.1.2 on 2024-11-12 18:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tide', '0010_alter_image_image_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SurfSpot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('station_id', models.CharField(max_length=10)),
                ('nickname', models.CharField(blank=True, max_length=100)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='surf_spots', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
