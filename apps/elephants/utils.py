"""
Utilities for elephant image generation
"""
import random
import re
from io import BytesIO
from pathlib import Path

import cairosvg
from django.conf import settings


def hex_to_rgb(hex_color: str) -> tuple:
    """
    Конвертация HEX цвета в RGB tuple

    Args:
        hex_color: Цвет в формате #RRGGBB

    Returns:
        Tuple (R, G, B)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Конвертация RGB в HEX цвет

    Args:
        r: Красный (0-255)
        g: Зелёный (0-255)
        b: Синий (0-255)

    Returns:
        Цвет в формате #RRGGBB
    """
    return f'#{r:02x}{g:02x}{b:02x}'.upper()


def generate_random_color() -> str:
    """
    Генерация случайного HEX цвета

    Returns:
        Случайный цвет в формате #RRGGBB
    """
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return rgb_to_hex(r, g, b)


def generate_color_from_hue(hue: int) -> str:
    """
    Генерация случайного цвета в заданном оттенке

    Args:
        hue: Оттенок от 0 до 360 (градусы на цветовом круге)
             0/360 = красный, 120 = зеленый, 240 = синий

    Returns:
        Цвет в формате #RRGGBB
    """
    import colorsys

    # Нормализуем hue в диапазон 0-1
    h = (hue % 360) / 360.0

    # Генерируем случайные значения насыщенности и яркости
    # Чтобы получить яркие, насыщенные цвета
    s = random.uniform(0.6, 1.0)  # Saturation 60-100%
    v = random.uniform(0.6, 1.0)  # Value/Brightness 60-100%

    # Конвертируем HSV в RGB
    r, g, b = colorsys.hsv_to_rgb(h, s, v)

    # Конвертируем в 0-255 диапазон
    r_int = int(r * 255)
    g_int = int(g * 255)
    b_int = int(b * 255)

    return rgb_to_hex(r_int, g_int, b_int)


def get_elephant_svg_template_path() -> Path:
    """
    Получить путь к SVG шаблону слона

    Returns:
        Path к файлу kupi_slona.svg
    """
    return Path(settings.BASE_DIR) / 'static' / 'images' / 'kupi_slona.svg'


def generate_colored_elephant(color_hex: str) -> BytesIO:
    """
    Генерация цветного изображения слона из SVG шаблона

    Загружает SVG шаблон, заменяет черный цвет на выбранный,
    конвертирует в PNG.

    Args:
        color_hex: Цвет в формате #RRGGBB

    Returns:
        BytesIO с PNG изображением
    """
    # Нормализуем цвет (uppercase)
    color_hex = color_hex.upper()

    # Загружаем SVG шаблон
    svg_path = get_elephant_svg_template_path()

    if not svg_path.exists():
        raise FileNotFoundError(f"SVG шаблон не найден: {svg_path}")

    # Читаем SVG как текст
    svg_content = svg_path.read_text(encoding='utf-8')

    # Заменяем черный цвет (#231f20) на выбранный цвет
    # Цвет слона в SVG - это fill="#231f20"
    svg_content = svg_content.replace('#231f20', color_hex.lower())
    svg_content = svg_content.replace('#231F20', color_hex.lower())

    # Также заменяем другие черные цвета
    svg_content = svg_content.replace('fill="#000000"', f'fill="{color_hex.lower()}"')

    # Конвертируем SVG в PNG
    # viewBox="220 160 1060 920" - пропорции примерно 1.15:1
    # Делаем квадратное изображение 1500x1500, cairosvg сам вписывает с сохранением пропорций
    png_data = cairosvg.svg2png(
        bytestring=svg_content.encode('utf-8'),
        output_width=1500,
        output_height=1500
    )

    # Возвращаем BytesIO
    output = BytesIO(png_data)
    output.seek(0)

    return output


def validate_hex_color(color_hex: str) -> bool:
    """
    Валидация HEX цвета

    Args:
        color_hex: Строка для проверки

    Returns:
        True если валидный HEX цвет
    """
    if not color_hex.startswith('#'):
        return False
    if len(color_hex) != 7:
        return False
    try:
        int(color_hex[1:], 16)
        return True
    except ValueError:
        return False
