"""
Views for payment pages
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import Order
from .yookassa_service import check_payment_status


@login_required
def payment_return(request):
    """
    Return page after YooKassa payment.
    Shows payment status and auto-redirects to dashboard.
    """
    order_id = request.GET.get('order_id')

    if not order_id:
        return redirect('/dashboard/')

    try:
        order = Order.objects.select_related('tariff').get(
            pk=order_id, user=request.user
        )
    except Order.DoesNotExist:
        return redirect('/dashboard/')

    # Check current status from YooKassa if still pending
    yookassa_status = None
    if order.status == 'pending' and order.yookassa_payment_id:
        yookassa_status = check_payment_status(order)

    context = {
        'order': order,
        'yookassa_status': yookassa_status,
    }
    return render(request, 'payments/return.html', context)
