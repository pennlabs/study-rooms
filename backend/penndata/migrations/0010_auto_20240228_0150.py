# Generated by Django 3.2.22 on 2024-02-28 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("penndata", "0009_auto_20240223_1820")]

    operations = [
        migrations.RemoveField(model_name="event", name="facebook"),
        migrations.AlterField(
            model_name="event", name="description", field=models.TextField(blank=True, null=True)
        ),
        migrations.AlterField(
            model_name="event",
            name="email",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="event", name="end", field=models.DateTimeField(blank=True, null=True)
        ),
        migrations.AlterField(
            model_name="event",
            name="event_type",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="event", name="image_url", field=models.URLField(blank=True, null=True)
        ),
        migrations.AlterField(
            model_name="event",
            name="location",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="event",
            name="website",
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
    ]
