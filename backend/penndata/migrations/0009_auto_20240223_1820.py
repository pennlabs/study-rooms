# Generated by Django 3.2.22 on 2024-02-23 23:20


from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("penndata", "0008_calendarevent"),
    ]

    operations = [
        migrations.RenameField(model_name="event", old_name="start_time", new_name="start",),
        migrations.RemoveField(model_name="event", name="end_time",),
        migrations.AddField(model_name="event", name="end", field=models.DateTimeField(null=True),),
        migrations.AddField(
            model_name="event", name="location", field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="event", name="description", field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name="event", name="email", field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="event",
            name="event_type",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="event", name="image_url", field=models.URLField(null=True),
        ),
    ]
