"""
Add yookassa_payment_id field and cancelled status to Order model
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_remove_order_payments_or_status_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='yookassa_payment_id',
            field=models.CharField(
                blank=True,
                max_length=50,
                null=True,
                unique=True,
                verbose_name='ID платежа YooKassa',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Ожидает оплаты'),
                    ('paid', 'Оплачен'),
                    ('processing', 'Генерация изображения'),
                    ('completed', 'Завершён'),
                    ('failed', 'Ошибка'),
                    ('cancelled', 'Отменён'),
                ],
                default='pending',
                max_length=20,
                verbose_name='Статус',
            ),
        ),
    ]
