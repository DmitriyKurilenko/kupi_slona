"""
Django admin for gifts app
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import GiftLink


@admin.register(GiftLink)
class GiftLinkAdmin(admin.ModelAdmin):
    """Admin для подарочных ссылок"""
    list_display = ('id', 'elephant_color', 'sender', 'recipient_name', 'is_claimed', 'claimed_by', 'created_at')
    list_filter = ('is_claimed', 'created_at')
    search_fields = ('sender__username', 'recipient_name', 'claimed_by__username')
    readonly_fields = ('id', 'uuid', 'created_at', 'claimed_at', 'public_url_display')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'uuid', 'elephant', 'sender')
        }),
        ('Получатель', {
            'fields': ('recipient_name', 'message')
        }),
        ('Статус', {
            'fields': ('is_claimed', 'claimed_by', 'claimed_at')
        }),
        ('Ссылка', {
            'fields': ('public_url_display',)
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )

    def elephant_color(self, obj):
        """Цвет слона"""
        if obj.elephant:
            return format_html(
                '<span style="display: inline-block; width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; margin-right: 5px;"></span>{}',
                obj.elephant.color_hex,
                obj.elephant.color_hex
            )
        return '-'
    elephant_color.short_description = 'Цвет слона'

    def public_url_display(self, obj):
        """Публичная ссылка"""
        url = obj.get_public_url()
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    public_url_display.short_description = 'Публичная ссылка'
