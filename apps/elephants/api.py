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
