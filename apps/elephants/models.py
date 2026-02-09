"""
Elephant model - unique colored elephant
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse

from .name_generator import generate_elephant_name


class Elephant(models.Model):
    """Купленный слон с уникальным цветом"""

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="elephants",
        verbose_name="Владелец"
    )
    order = models.OneToOneField(
        "payments.Order",
        on_delete=models.CASCADE,
        verbose_name="Заказ"
    )
    color_hex = models.CharField(
        max_length=7,
        unique=True,
        verbose_name="Цвет (HEX)",
        help_text="Уникальный цвет в формате #RRGGBB"
    )
    color_r = models.PositiveSmallIntegerField(
        verbose_name="Красный (R)"
    )
    color_g = models.PositiveSmallIntegerField(
        verbose_name="Зелёный (G)"
    )
    color_b = models.PositiveSmallIntegerField(
        verbose_name="Синий (B)"
    )
    image = models.ImageField(
        upload_to="elephants/%Y/%m/",
        verbose_name="Изображение"
    )
    is_gifted = models.BooleanField(
        default=False,
        verbose_name="Подарен"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Слон"
        verbose_name_plural = "Слоны"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=["color_hex"],
                name="unique_elephant_color"
            )
        ]

    def __str__(self):
        return f"Elephant {self.color_hex} - {self.owner.username}"

    def clean(self):
        """Валидация модели"""
        super().clean()

        # Проверка формата HEX
        if not self.color_hex.startswith('#') or len(self.color_hex) != 7:
            raise ValidationError({
                'color_hex': 'Цвет должен быть в формате #RRGGBB'
            })

        # Проверка валидности HEX кода
        try:
            int(self.color_hex[1:], 16)
        except ValueError:
            raise ValidationError({
                'color_hex': 'Некорректный HEX код цвета'
            })

        # Проверка диапазона RGB значений
        if not (0 <= self.color_r <= 255):
            raise ValidationError({'color_r': 'Значение должно быть от 0 до 255'})
        if not (0 <= self.color_g <= 255):
            raise ValidationError({'color_g': 'Значение должно быть от 0 до 255'})
        if not (0 <= self.color_b <= 255):
            raise ValidationError({'color_b': 'Значение должно быть от 0 до 255'})

    def save(self, *args, **kwargs):
        """Автоматически разбираем HEX в RGB компоненты"""
        if self.color_hex:
            # Конвертация HEX в RGB
            hex_color = self.color_hex.lstrip('#')
            self.color_r = int(hex_color[0:2], 16)
            self.color_g = int(hex_color[2:4], 16)
            self.color_b = int(hex_color[4:6], 16)

        self.full_clean()
        super().save(*args, **kwargs)

    def get_color_display(self):
        """Возвращает строковое представление цвета в RGB"""
        return f"RGB({self.color_r}, {self.color_g}, {self.color_b})"

    def get_name(self):
        """Возвращает уникальное имя слона на основе его цвета"""
        return generate_elephant_name(self.color_hex)

    def can_be_gifted(self):
        """Может ли слон быть подарен"""
        return not self.is_gifted

    def get_download_url(self):
        """URL для скачивания изображения"""
        return reverse('elephant-download', kwargs={'pk': self.pk})

    def mark_as_gifted(self):
        """Отметить слона как подаренного"""
        self.is_gifted = True
        self.save(update_fields=['is_gifted'])

    def transfer_ownership(self, new_owner):
        """Передать слона новому владельцу"""
        self.owner = new_owner
        self.is_gifted = True
        self.save(update_fields=['owner', 'is_gifted'])
