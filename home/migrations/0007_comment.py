# Generated by Django 4.2.7 on 2024-03-07 01:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_remove_contributions_status_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True, null=True)),
                ('createAt', models.DateTimeField(auto_now_add=True)),
                ('contribution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.contributions')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.userprofile')),
            ],
        ),
    ]
