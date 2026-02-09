"""
Django admin for elephants app
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Elephant


@admin.register(Elephant)
class ElephantAdmin(admin.ModelAdmin):
    """Admin для слонов"""
    list_display = ('id', 'elephant_name', 'color_preview', 'color_hex', 'owner', 'is_gifted', 'created_at')
    list_filter = ('is_gifted', 'created_at')
    search_fields = ('color_hex', 'owner__username')
    readonly_fields = ('id', 'elephant_name', 'color_r', 'color_g', 'color_b', 'created_at', 'color_preview', 'image_preview')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'elephant_name', 'owner', 'order', 'is_gifted')
        }),
        ('Цвет', {
            'fields': ('color_hex', 'color_r', 'color_g', 'color_b', 'color_preview')
        }),
        ('Изображение', {
            'fields': ('image', 'image_preview')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )

    def elephant_name(self, obj):
        """Имя слона"""
        return obj.get_name()
    elephant_name.short_description = 'Имя'

    def color_preview(self, obj):
        """Превью цвета в admin"""
        return format_html(
            '<div style="width: 50px; height: 30px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color_hex
        )
    color_preview.short_description = 'Цвет'

    def image_preview(self, obj):
        """Превью изображения в admin"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.image.url
            )
        return 'Нет изображения'
    image_preview.short_description = 'Превью'
