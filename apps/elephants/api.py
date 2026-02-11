"""
API endpoints for elephants
"""
import re

from ninja import Router, Query
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse

from .models import Elephant
from .services import get_user_elephants, get_elephant_by_id
from .schemas import ElephantListSchema, ElephantDetailSchema, ElephantLookupSchema
from apps.accounts.schemas import MessageSchema
from apps.core.auth import auth

router = Router()


@router.get("/", response={200: list[ElephantListSchema], 401: MessageSchema}, auth=auth)
def list_elephants(request):
    """Список слонов текущего пользователя"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    elephants = get_user_elephants(request.user)
    return 200, list(elephants)


@router.get("/{elephant_id}", response={200: ElephantDetailSchema, 401: MessageSchema, 403: MessageSchema, 404: MessageSchema}, auth=auth)
def get_elephant(request, elephant_id: int):
    """Детали слона"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    try:
        elephant = get_elephant_by_id(elephant_id, request.user)
        return 200, elephant
    except Elephant.DoesNotExist:
        return 404, {"message": "Слон не найден"}
    except PermissionError as e:
        return 403, {"message": str(e)}


@router.get("/{elephant_id}/download", response={200: None, 401: MessageSchema, 403: MessageSchema, 404: MessageSchema}, auth=auth)
def download_elephant(request, elephant_id: int):
    """Скачать изображение слона"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    try:
        elephant = get_elephant_by_id(elephant_id, request.user)

        # Проверка наличия изображения
        if not elephant.image:
            return 404, {"message": "Изображение не найдено"}

        # Возвращаем файл
        response = FileResponse(
            elephant.image.open('rb'),
            content_type='image/png'
        )
        response['Content-Disposition'] = f'attachment; filename="elephant_{elephant.color_hex.lstrip("#")}.png"'
        return response

    except Elephant.DoesNotExist:
        return 404, {"message": "Слон не найден"}
    except PermissionError:
        return 403, {"message": "Доступ запрещён"}


@router.get("/lookup/", response={200: ElephantLookupSchema, 404: MessageSchema})
def lookup_elephant(request, q: str = Query(...)):
    """Public lookup: find elephant by color hex or name (case-insensitive)"""
    query = q.strip()
    if not query:
        return 404, {"message": "Введите цвет или имя слона"}

    # Try as HEX color
    hex_match = re.match(r'^#?([0-9a-fA-F]{6})$', query)
    if hex_match:
        color_hex = f"#{hex_match.group(1).upper()}"
        try:
            elephant = Elephant.objects.select_related('owner').get(color_hex=color_hex)
            return 200, elephant
        except Elephant.DoesNotExist:
            return 404, {"message": f"Слон с цветом {color_hex} не найден. Этот цвет ещё свободен!"}

    # Search by name (case-insensitive)
    query_lower = query.lower()
    for elephant in Elephant.objects.select_related('owner').all():
        if elephant.get_name().lower() == query_lower:
            return 200, elephant

    # Partial match
    results = []
    for elephant in Elephant.objects.select_related('owner').all():
        if query_lower in elephant.get_name().lower():
            results.append(elephant)

    if len(results) == 1:
        return 200, results[0]
    elif len(results) > 1:
        return 404, {"message": f"Найдено {len(results)} слонов. Уточните запрос."}

    return 404, {"message": "Слон не найден"}
