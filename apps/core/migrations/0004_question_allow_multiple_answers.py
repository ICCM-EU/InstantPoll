# Generated by Django 4.0 on 2022-01-19 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_event_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='allow_multiple_answers',
            field=models.BooleanField(default=False, verbose_name='multiple answers allowed'),
        ),
    ]