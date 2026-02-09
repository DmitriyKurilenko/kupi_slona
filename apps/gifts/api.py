"""
API endpoints for gifts
"""
from ninja import Router
from django.core.exceptions import ValidationError
from uuid import UUID

from .models import GiftLink
from .services import create_gift_link, claim_gift, get_user_sent_gifts, get_gift_by_uuid, can_user_claim_gift
from .schemas import CreateGiftSchema, GiftLinkSchema, PublicGiftSchema, ClaimGiftResponseSchema
from apps.accounts.schemas import MessageSchema
from apps.elephants.models import Elephant
from apps.core.auth import auth

router = Router()


@router.post("/", response={201: GiftLinkSchema, 400: MessageSchema, 401: MessageSchema, 403: MessageSchema}, auth=auth)
def create_gift(request, payload: CreateGiftSchema):
    """Создать подарочную ссылку"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    try:
        gift_link = create_gift_link(
            elephant_id=payload.elephant_id,
            sender=request.user,
            sender_name=payload.sender_name,
            recipient_name=payload.recipient_name,
            message=payload.message
        )
        return 201, gift_link

    except Elephant.DoesNotExist:
        return 400, {"message": "Слон не найден"}
    except PermissionError as e:
        return 403, {"message": str(e)}
    except ValidationError as e:
        return 400, {"message": str(e)}
    except Exception as e:
        return 400, {"message": str(e)}


@router.get("/sent", response={200: list[GiftLinkSchema], 401: MessageSchema}, auth=auth)
def list_sent_gifts(request):
    """Список отправленных подарков"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    gifts = get_user_sent_gifts(request.user)
    return 200, list(gifts)


@router.get("/public/{uuid}", response={200: PublicGiftSchema, 404: MessageSchema})
def get_public_gift(request, uuid: UUID):
    """Публичная информация о подарке"""
    try:
        gift = get_gift_by_uuid(uuid)
        return 200, gift
    except GiftLink.DoesNotExist:
        return 404, {"message": "Подарок не найден"}


@router.post("/public/{uuid}/claim", response={200: ClaimGiftResponseSchema, 400: MessageSchema, 401: MessageSchema}, auth=auth)
def claim_public_gift(request, uuid: UUID):
    """Принять подарок"""
    # Auth handled by decorator - request.user is guaranteed authenticated
    try:
        # Получаем подарок
        gift = get_gift_by_uuid(uuid)

        # Проверяем возможность принятия
        can_claim, reason = can_user_claim_gift(gift, request.user)
        if not can_claim:
            return 400, {"message": reason}

        # Принимаем подарок
        elephant = claim_gift(uuid, request.user)

        return 200, {
            "success": True,
            "message": "Подарок успешно принят!",
            "elephant_id": elephant.id
        }

    except GiftLink.DoesNotExist:
        return 400, {"message": "Подарок не найден"}
    except ValueError as e:
        return 400, {"message": str(e)}
    except Exception as e:
        return 400, {"message": str(e)}
