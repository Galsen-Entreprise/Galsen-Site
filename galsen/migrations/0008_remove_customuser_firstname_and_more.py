# Generated by Django 5.0.2 on 2024-03-16 14:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('galsen', '0007_customuser_firstname_customuser_lastname'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='firstname',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='lastname',
        ),
    ]
