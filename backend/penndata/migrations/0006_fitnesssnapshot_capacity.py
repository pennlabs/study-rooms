# Generated by Django 3.2.18 on 2023-03-19 22:03


from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("penndata", "0005_fitnessroom_fitnesssnapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="fitnesssnapshot", name="capacity", field=models.FloatField(null=True),
        ),
    ]
