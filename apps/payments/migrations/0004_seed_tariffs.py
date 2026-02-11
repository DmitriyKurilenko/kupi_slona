"""
Data migration to seed initial tariffs.
Creates 'basic' and 'advanced' tariffs if they don't exist.
"""
from django.db import migrations


def create_tariffs(apps, schema_editor):
    Tariff = apps.get_model('payments', 'Tariff')
    tariffs = [
        {
            'name': 'basic',
            'price': 99.00,
            'description': 'Случайный цвет слона. Вы получите уникального слона случайного цвета.',
            'is_active': True,
        },
        {
            'name': 'advanced',
            'price': 299.00,
            'description': 'Выберите свой цвет! Укажите точный HEX-цвет (#RRGGBB) или оттенок (HUE:0-360).',
            'is_active': True,
        },
    ]
    for tariff_data in tariffs:
        Tariff.objects.get_or_create(
            name=tariff_data['name'],
            defaults=tariff_data,
        )


def remove_tariffs(apps, schema_editor):
    Tariff = apps.get_model('payments', 'Tariff')
    Tariff.objects.filter(name__in=['basic', 'advanced']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_add_indexes'),
    ]

    operations = [
        migrations.RunPython(create_tariffs, remove_tariffs),
    ]
