"""
Business logic services for elephants
"""
from django.db import transaction
from django.core.files.base import ContentFile

from .models import Elephant
from .utils import generate_colored_elephant


def check_color_availability(color_hex: str) -> bool:
    """
    Проверка доступности цвета

    Args:
        color_hex: Цвет в формате #RRGGBB

    Returns:
        True если цвет доступен (не занят)
    """
    return not Elephant.objects.filter(color_hex=color_hex.upper()).exists()


@transaction.atomic
def create_elephant(order, color_hex: str, image_bytes=None) -> Elephant:
    """
    Создание нового слона

    Args:
        order: Order объект
        color_hex: Цвет в формате #RRGGBB
        image_bytes: BytesIO с изображением (опционально, будет сгенерировано если None)

    Returns:
        Созданный Elephant объект

    Raises:
        ValueError: Если цвет уже занят (relies on database-level uniqueness constraint)
    """
    from django.db import IntegrityError

    # Нормализуем цвет
    color_hex = color_hex.upper()

    # Генерируем изображение если не передано
    if image_bytes is None:
        image_bytes = generate_colored_elephant(color_hex)

    try:
        # Создаём объект слона
        elephant = Elephant(
            owner=order.user,
            order=order,
            color_hex=color_hex
        )

        # Сохраняем изображение
        filename = f"elephant_{color_hex.lstrip('#')}.png"
        elephant.image.save(filename, ContentFile(image_bytes.read()), save=False)

        # Сохраняем объект (save() автоматически распарсит HEX в RGB)
        # Database UniqueConstraint on color_hex ensures atomicity - no race condition
        elephant.save()

        return elephant

    except IntegrityError as e:
        # Check if it's the color uniqueness violation
        if 'unique_elephant_color' in str(e).lower() or 'color_hex' in str(e).lower():
            raise ValueError(f"Цвет {color_hex} уже занят другим слоном")
        # Re-raise if it's a different integrity error
        raise


def get_user_elephants(user):
    """
    Получить список слонов пользователя (собственных и подаренных другим)

    Args:
        user: User объект

    Returns:
        QuerySet с слонами пользователя (owned=True) и подаренными (owned=False)
    """
    from django.db.models import Q, Case, When, Value, BooleanField

    # Получаем слонов которыми владеет пользователь ИЛИ которых он подарил и они были приняты
    elephants = Elephant.objects.filter(
        Q(owner=user) | Q(gift_link__sender=user, gift_link__is_claimed=True)
    ).annotate(
        is_owned_by_user=Case(
            When(owner=user, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    ).distinct().select_related('order', 'order__tariff', 'gift_link', 'gift_link__claimed_by').order_by('-created_at')

    return elephants


def get_elephant_by_id(elephant_id: int, user=None):
    """
    Получить слона по ID с опциональной проверкой владельца

    Args:
        elephant_id: ID слона
        user: User объект для проверки владения (опционально)

    Returns:
        Elephant объект или None

    Raises:
        Elephant.DoesNotExist: Если слон не найден
        PermissionError: Если пользователь не владелец
    """
    elephant = Elephant.objects.select_related('order').get(pk=elephant_id)

    if user and elephant.owner != user:
        raise PermissionError("Вы не являетесь владельцем этого слона")

    return elephant


def get_available_colors_count() -> int:
    """
    Получить количество доступных цветов

    Returns:
        Количество свободных цветов (из 16777216 возможных RGB комбинаций)
    """
    total_colors = 256 * 256 * 256  # 16,777,216
    used_colors = Elephant.objects.count()
    return total_colors - used_colors
