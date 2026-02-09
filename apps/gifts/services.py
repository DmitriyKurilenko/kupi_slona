"""
Business logic services for gifts
"""
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import GiftLink
from apps.elephants.models import Elephant


@transaction.atomic
def create_gift_link(elephant_id: int, sender, sender_name: str = "", recipient_name: str = "", message: str = "") -> GiftLink:
    """
    Создание подарочной ссылки

    Args:
        elephant_id: ID слона
        sender: User объект отправителя
        sender_name: Отображаемое имя отправителя (опционально, по умолчанию username)
        recipient_name: Имя получателя (опционально)
        message: Персональное сообщение (опционально)

    Returns:
        Созданный GiftLink объект

    Raises:
        Elephant.DoesNotExist: Если слон не найден
        PermissionError: Если отправитель не владелец
        ValidationError: Если слон уже подарен
    """
    # Получаем слона
    elephant = Elephant.objects.select_related('owner').get(pk=elephant_id)

    # Проверка владения
    if elephant.owner != sender:
        raise PermissionError("Вы не являетесь владельцем этого слона")

    # Проверка, что слон ещё не подарен
    if elephant.is_gifted:
        raise ValidationError("Этот слон уже был подарен")

    # Проверка, что для этого слона ещё нет активной подарочной ссылки
    if hasattr(elephant, 'gift_link'):
        raise ValidationError("Для этого слона уже создана подарочная ссылка")

    # Если sender_name не указан, используем username
    if not sender_name:
        sender_name = sender.username

    # Создаём подарочную ссылку
    gift_link = GiftLink.objects.create(
        elephant=elephant,
        sender=sender,
        sender_name=sender_name,
        recipient_name=recipient_name,
        message=message
    )

    # Отмечаем слона как подаренного (но владелец пока не меняется)
    elephant.mark_as_gifted()

    return gift_link


@transaction.atomic
def claim_gift(gift_uuid, user) -> Elephant:
    """
    Принять подарок

    Args:
        gift_uuid: UUID подарочной ссылки
        user: User объект получателя

    Returns:
        Elephant объект

    Raises:
        GiftLink.DoesNotExist: Если подарок не найден
        ValueError: Если подарок уже принят или нельзя принять свой подарок
    """
    # Получаем подарочную ссылку
    gift_link = GiftLink.objects.select_related('elephant', 'sender').get(uuid=gift_uuid)

    # Принимаем подарок (включает проверки и передачу владения)
    elephant = gift_link.claim(user)

    return elephant


def get_user_sent_gifts(user):
    """
    Получить список отправленных подарков

    Args:
        user: User объект

    Returns:
        QuerySet с отправленными подарками
    """
    return GiftLink.objects.filter(sender=user).select_related('elephant', 'claimed_by')


def get_user_received_gifts(user):
    """
    Получить список полученных подарков

    Args:
        user: User объект

    Returns:
        QuerySet с полученными подарками
    """
    return GiftLink.objects.filter(claimed_by=user).select_related('elephant', 'sender')


def get_gift_by_uuid(gift_uuid):
    """
    Получить подарок по UUID

    Args:
        gift_uuid: UUID подарочной ссылки

    Returns:
        GiftLink объект

    Raises:
        GiftLink.DoesNotExist: Если подарок не найден
    """
    return GiftLink.objects.select_related('elephant', 'sender', 'claimed_by').get(uuid=gift_uuid)


def can_user_claim_gift(gift_link, user) -> tuple:
    """
    Проверка, может ли пользователь принять подарок

    Args:
        gift_link: GiftLink объект
        user: User объект или None (неавторизованный)

    Returns:
        Tuple (can_claim: bool, reason: str)
    """
    # Проверка авторизации
    if not user or not user.is_authenticated:
        return False, "Необходимо войти в систему"

    # Проверка, что подарок не принят
    if not gift_link.can_be_claimed():
        return False, "Подарок уже был принят"

    # Проверка, что это не свой подарок
    if user == gift_link.sender:
        return False, "Нельзя принять свой собственный подарок"

    return True, "Можно принять"
