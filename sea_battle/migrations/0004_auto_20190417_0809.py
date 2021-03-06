# Generated by Django 2.1.7 on 2019-04-17 08:09
import json

from django.db import migrations


def convert_data_to_json(apps, schema_editor):
    Battlemap = apps.get_model('sea_battle', 'battlemap')
    for obj in Battlemap.objects.all():
        data = [ship for ship in json.loads(obj.fleet_new)]
        obj.fleet_new = data
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('sea_battle', '0003_auto_20190416_1638'),
    ]

    operations = [
        migrations.RunPython(convert_data_to_json),
    ]
