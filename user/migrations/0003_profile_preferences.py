# Generated by Django 3.1.6 on 2021-02-18 23:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laundry', '0001_initial'),
        ('user', '0002_auto_20210205_1851'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='preferences',
            field=models.ManyToManyField(to='laundry.LaundryRoom'),
        ),
    ]
