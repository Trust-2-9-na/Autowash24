# Generated by Django 5.0.6 on 2024-06-07 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autowash', '0003_remove_systemstatus_on_off_button_status_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('url', models.CharField(max_length=200)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
