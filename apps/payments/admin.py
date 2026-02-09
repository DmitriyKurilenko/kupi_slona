"""
Django admin for payments app
"""
from django.contrib import admin
from .models import Tariff, Order


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    """Admin для тарифов"""
    list_display = ('name', 'price', 'is_active')
    list_filter = ('is_active', 'name')
    search_fields = ('name', 'description')
    readonly_fields = ('id',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin для заказов"""
    list_display = ('id', 'user', 'tariff', 'status', 'desired_color', 'created_at', 'paid_at')
    list_filter = ('status', 'tariff', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'user', 'tariff', 'status')
        }),
        ('Цвет', {
            'fields': ('desired_color',),
            'description': 'Только для advanced тарифа'
        }),
        ('Даты', {
            'fields': ('created_at', 'paid_at')
        }),
    )
