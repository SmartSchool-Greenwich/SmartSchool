# Generated by Django 4.2.7 on 2024-03-07 06:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0009_academicyear_faculties'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='faculty',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='home.faculties'),
        ),
    ]
