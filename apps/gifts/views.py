"""
Views for gift pages
"""
from django.shortcuts import render, get_object_or_404
from django.views import View
from .models import GiftLink


class PublicGiftView(View):
    """Публичная страница подарка"""
    template_name = 'gifts/public_gift.html'

    def get(self, request, uuid):
        gift = get_object_or_404(GiftLink, uuid=uuid)
        context = {
            'gift': gift,
            'page_title': f'Подарок от {gift.sender.username}',
            'can_claim': not gift.is_claimed and request.user.is_authenticated and request.user != gift.sender
        }
        return render(request, self.template_name, context)
