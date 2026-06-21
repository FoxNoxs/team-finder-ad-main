import io
import random

from PIL import Image, ImageDraw, ImageFont


# --- Телефон ---
PHONE_PREFIX_8 = '8'
PHONE_PREFIX_PLUS7 = '+7'
PHONE_LENGTH_RU = 11


# --- Аватарка ---
AVATAR_SIZE = 200
AVATAR_FONT_SIZE = 100
AVATAR_DEFAULT_LETTER = 'U'
AVATAR_FONT_PATH = 'static/fonts/Raleway-Regular.ttf'
AVATAR_IMAGE_FORMAT = 'PNG'
AVATAR_IMAGE_MODE = 'RGB'

# Цвета фона (RGB)
COLOR_CORNFLOWER_BLUE = (100, 149, 237)
COLOR_LIGHT_GREEN = (144, 238, 144)
COLOR_LIGHT_PINK = (255, 182, 193)
COLOR_LIGHT_ORANGE = (255, 165, 79)
COLOR_MEDIUM_PURPLE = (147, 112, 219)
COLOR_TURQUOISE = (64, 224, 208)
COLOR_SKY_BLUE = (135, 206, 235)
COLOR_WHITE = (255, 255, 255)

AVATAR_BG_COLORS = [
    COLOR_CORNFLOWER_BLUE,
    COLOR_LIGHT_GREEN,
    COLOR_LIGHT_PINK,
    COLOR_LIGHT_ORANGE,
    COLOR_MEDIUM_PURPLE,
    COLOR_TURQUOISE,
    COLOR_SKY_BLUE,
]
AVATAR_TEXT_COLOR = COLOR_WHITE

# Позиционирование
HALF_DIVISOR = 2
BBOX_X_INDEX = 0
BBOX_Y_INDEX = 1
BBOX_RIGHT_INDEX = 2
BBOX_BOTTOM_INDEX = 3


def normalize_phone(phone):
    """Приводит номер телефона к формату +7XXXXXXXXXX."""
    if phone.startswith(PHONE_PREFIX_8) and len(phone) == PHONE_LENGTH_RU:
        return PHONE_PREFIX_PLUS7 + phone[1:]
    return phone


def generate_avatar(letter):
    """Генерирует аватарку с первой буквой имени."""
    bg_color = random.choice(AVATAR_BG_COLORS)

    img = Image.new(
        AVATAR_IMAGE_MODE,
        (AVATAR_SIZE, AVATAR_SIZE),
        color=bg_color,
    )
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(AVATAR_FONT_PATH, size=AVATAR_FONT_SIZE)
    except Exception:
        font = ImageFont.load_default(size=AVATAR_FONT_SIZE)

    letter = letter.upper()
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[BBOX_RIGHT_INDEX] - bbox[BBOX_X_INDEX]
    text_height = bbox[BBOX_BOTTOM_INDEX] - bbox[BBOX_Y_INDEX]
    x = (AVATAR_SIZE - text_width) / HALF_DIVISOR - bbox[BBOX_X_INDEX]
    y = (AVATAR_SIZE - text_height) / HALF_DIVISOR - bbox[BBOX_Y_INDEX]
    draw.text((x, y), letter, fill=AVATAR_TEXT_COLOR, font=font)

    output = io.BytesIO()
    img.save(output, format=AVATAR_IMAGE_FORMAT)
    output.seek(0)
    return output
