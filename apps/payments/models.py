"""
Payment models: Tariff and Order
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Tariff(models.Model):
    """Тарифные планы для покупки слонов"""

    BASIC = "basic"
    ADVANCED = "advanced"
    TARIFF_CHOICES = [
        (BASIC, "Базовый"),  # Рандомный цвет
        (ADVANCED, "Продвинутый"),  # Выбор оттенка
    ]

    name = models.CharField(
        max_length=20,
        choices=TARIFF_CHOICES,
        unique=True,
        verbose_name="Название тарифа"
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Цена"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"
        ordering = ['price']

    def __str__(self):
        return f"{self.get_name_display()} - ${self.price}"


class Order(models.Model):
    """Заказ на покупку слона"""

    STATUS_CHOICES = [
        ("pending", "Ожидает оплаты"),
        ("paid", "Оплачен"),
        ("processing", "Генерация изображения"),
        ("completed", "Завершён"),
        ("failed", "Ошибка"),
        ("cancelled", "Отменён"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Пользователь"
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.PROTECT,
        verbose_name="Тариф"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Статус"
    )
    desired_color = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Желаемый цвет (HEX) или оттенок",
        help_text="Только для advanced тарифа, формат: #RRGGBB или HUE:XXX"
    )
    yookassa_payment_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        verbose_name="ID платежа YooKassa",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата оплаты"
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.status}"

    def clean(self):
        """Валидация заказа - только базовая проверка формата"""
        super().clean()

        # Business logic validation moved to services.py (single source of truth)
        # Only basic format check here to maintain data integrity
        if self.desired_color and self.tariff:
            # Basic format check: should be either #RRGGBB or HUE:XXX
            if not (self.desired_color.startswith('#') or self.desired_color.startswith('HUE:')):
                raise ValidationError({
                    'desired_color': 'Формат должен быть #RRGGBB или HUE:XXX'
                })

    def save(self, *args, **kwargs):
        # Validation should happen in service layer, not on every save
        # This allows more control and prevents duplication
        super().save(*args, **kwargs)

    def mark_as_paid(self):
        """Отметить заказ как оплаченный"""
        self.status = "paid"
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at'])

    def can_be_processed(self):
        """Может ли заказ быть обработан"""
        return self.status == "paid"

    def is_completed(self):
        """Завершён ли заказ"""
        return self.status == "completed"

    def mark_as_processing(self):
        """Отметить заказ как обрабатываемый"""
        self.status = "processing"
        self.save(update_fields=['status'])

    def mark_as_completed(self):
        """Отметить заказ как завершённый"""
        self.status = "completed"
        self.save(update_fields=['status'])

    def mark_as_failed(self):
        """Отметить заказ как проваленный"""
        self.status = "failed"
        self.save(update_fields=['status'])

    def mark_as_cancelled(self):
        """Отметить заказ как отменённый"""
        self.status = "cancelled"
        self.save(update_fields=['status'])
