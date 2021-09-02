# Generated by Django 3.2.5 on 2021-09-02 21:41

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("gsr_booking", "0002_auto_20210129_1527"),
    ]

    operations = [
        migrations.CreateModel(
            name="GSR",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[("WHARTON", "Wharton"), ("LIBCAL", "Libcal")],
                        default="LIBCAL",
                        max_length=7,
                    ),
                ),
                ("lid", models.IntegerField()),
                ("gid", models.IntegerField(null=True)),
                ("name", models.CharField(max_length=255)),
                ("image_url", models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name="GSRBooking",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("booking_id", models.CharField(blank=True, max_length=255, null=True)),
                ("room_id", models.IntegerField()),
                ("room_name", models.CharField(max_length=255)),
                ("start", models.DateTimeField(default=django.utils.timezone.now)),
                ("end", models.DateTimeField(default=django.utils.timezone.now)),
                ("is_cancelled", models.BooleanField(default=False)),
                ("reminder_sent", models.BooleanField(default=False)),
                (
                    "gsr",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="gsr_booking.gsr"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
