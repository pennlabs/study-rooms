# Generated by Django 3.2.7 on 2022-01-12 20:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0005_auto_20211231_1558"),
    ]

    operations = [
        migrations.RenameField(
            model_name="post", old_name="user_comment", new_name="club_comment",
        ),
        migrations.RenameField(model_name="post", old_name="created_at", new_name="created_date",),
        migrations.RemoveField(model_name="post", name="approved",),
        migrations.RemoveField(model_name="post", name="source",),
        migrations.RemoveField(model_name="post", name="user",),
        migrations.AddField(
            model_name="post", name="club_code", field=models.CharField(blank=True, max_length=255),
        ),
    ]
