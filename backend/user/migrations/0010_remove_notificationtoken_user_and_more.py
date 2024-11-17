# Generated by Django 5.0.2 on 2024-11-11 05:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0009_profile_fitness_preferences"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="notificationtoken",
            name="user",
        ),
        migrations.CreateModel(
            name="AndroidNotificationToken",
            fields=[
                ("token", models.CharField(max_length=255, primary_key=True, serialize=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="IOSNotificationToken",
            fields=[
                ("token", models.CharField(max_length=255, primary_key=True, serialize=False)),
                ("is_dev", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="NotificationService",
            fields=[
                ("name", models.CharField(max_length=255, primary_key=True, serialize=False)),
                ("enabled_users", models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name="NotificationSetting",
        ),
        migrations.DeleteModel(
            name="NotificationToken",
        ),
    ]
