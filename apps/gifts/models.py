"""
Gift model for gifting elephants
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone


class GiftLink(models.Model):
    """Уникальная ссылка для подарка слона"""

    elephant = models.OneToOneField(
        "elephants.Elephant",
        on_delete=models.CASCADE,
        related_name="gift_link",
        verbose_name="Слон"
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Уникальный идентификатор"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_gifts",
        verbose_name="Отправитель"
    )
    sender_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Имя отправителя",
        help_text="Отображаемое имя отправителя (по умолчанию username)"
    )
    recipient_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Имя получателя"
    )
    message = models.TextField(
        blank=True,
        verbose_name="Сообщение",
        help_text="Персональное сообщение для получателя"
    )
    is_claimed = models.BooleanField(
        default=False,
        verbose_name="Принят"
    )
    claimed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="received_gifts",
        verbose_name="Принят пользователем"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    claimed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата принятия"
    )

    class Meta:
        verbose_name = "Подарочная ссылка"
        verbose_name_plural = "Подарочные ссылки"
        ordering = ['-created_at']

    def __str__(self):
        status = "Принят" if self.is_claimed else "Ожидает"
        return f"Gift {self.uuid} - {status}"

    def get_public_url(self):
        """Получить публичную URL ссылку"""
        return reverse("gift-page", kwargs={"uuid": self.uuid})

    def can_be_claimed(self):
        """Может ли подарок быть принят"""
        return not self.is_claimed

    def claim(self, user):
        """Принять подарок"""
        if not self.can_be_claimed():
            raise ValueError("Подарок уже был принят")

        if user == self.sender:
            raise ValueError("Нельзя принять свой собственный подарок")

        # Передать слона новому владельцу
        self.elephant.transfer_ownership(user)

        # Отметить подарок как принятый
        self.is_claimed = True
        self.claimed_by = user
        self.claimed_at = timezone.now()
        self.save(update_fields=['is_claimed', 'claimed_by', 'claimed_at'])

        return self.elephant

    def get_recipient_display(self):
        """Отображение получателя"""
        if self.is_claimed and self.claimed_by:
            return self.claimed_by.username
        elif self.recipient_name:
            return self.recipient_name
        else:
            return "Не указан"
