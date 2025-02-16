# card_generator.py
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# Пути к файлам (относительно корня проекта)
BACKGROUND_PATH = os.path.join("static", "images", "background.jpg")
DEFAULT_PHOTO_PATH = os.path.join("static", "images", "default_photo.jpg")

# Шрифты – убедитесь, что arial.ttf доступен или укажите путь к другому шрифту.
FONT_TITLE = ImageFont.truetype("arial.ttf", 40)
FONT_SUBTITLE = ImageFont.truetype("arial.ttf", 25)
FONT_TEXT = ImageFont.truetype("arial.ttf", 22)

# Максимальная ширина текста (в пикселях)
TEXT_WIDTH = 900

def wrap_text(text, width=40):
    """
    Функция для автоматического переноса строк по количеству символов.
    """
    lines = []
    for line in text.split("\n"):
        wrapped_lines = textwrap.wrap(line, width=width)
        lines.extend(wrapped_lines)
    return lines

def draw_wrapped_text(draw, text, position, font, fill="black", max_width=TEXT_WIDTH):
    """
    Рисует текст с автопереносом строк.
    Возвращает конечную координату y.
    """
    x, y = position
    lines = wrap_text(text, width=40)
    for line in lines:
        draw.text((x, y), line, fill=fill, font=font)
        y += font.size + 5  # Интервал между строками
    return y

def generate_memorial_card(data, output_path):
    """
    Генерирует мемориальную карточку по данным и сохраняет её в output_path.
    data – словарь с полями: full_name, birth_date, death_date, photo_path, description,
           burial_place, awards (список или строка), military_service.
    """
    # Открываем фон карточки
    background = Image.open(BACKGROUND_PATH).convert("RGB")
    draw = ImageDraw.Draw(background)
    width, height = background.size

    # Загружаем фото или используем заглушку
    photo_path = data.get("photo_path") or DEFAULT_PHOTO_PATH
    try:
        photo = Image.open(photo_path).convert("RGB").resize((250, 300))
    except Exception as e:
        photo = Image.open(DEFAULT_PHOTO_PATH).convert("RGB").resize((250, 300))

    # Рисуем ФИО в центре сверху
    full_name = data.get("full_name", "Неизвестный")
    bbox = draw.textbbox((0, 0), full_name, font=FONT_TITLE)
    title_x = width // 2 - (bbox[2] - bbox[0]) // 2
    draw.text((title_x, 30), full_name, fill="black", font=FONT_TITLE)

    # Рисуем даты (если заданы)
    birth_date = data.get("birth_date", "")
    death_date = data.get("death_date", "")
    date_text = f"{birth_date} – {death_date}" if (birth_date or death_date) else ""
    if date_text:
        bbox = draw.textbbox((0, 0), date_text, font=FONT_SUBTITLE)
        date_x = width // 2 - (bbox[2] - bbox[0]) // 2
        draw.text((date_x, 80), date_text, fill="black", font=FONT_SUBTITLE)

    # Центрируем и вставляем фото
    photo_x = width // 2 - photo.width // 2
    background.paste(photo, (photo_x, 130))

    # Рисуем текстовые блоки ниже фото
    text_x = 50
    text_y = 450

    if data.get("description"):
        text_y = draw_wrapped_text(draw, f"Описание: {data['description']}", (text_x, text_y), FONT_TEXT)
    if data.get("burial_place"):
        text_y = draw_wrapped_text(draw, f"Место захоронения: {data['burial_place']}", (text_x, text_y), FONT_TEXT)
    if data.get("awards"):
        awards_val = data["awards"]
        if isinstance(awards_val, list):
            awards_str = ", ".join(awards_val)
        else:
            awards_str = awards_val
        text_y = draw_wrapped_text(draw, f"Награды: {awards_str}", (text_x, text_y), FONT_TEXT)
    if data.get("military_service"):
        text_y = draw_wrapped_text(draw, f"Участие в военных событиях: {data['military_service']}", (text_x, text_y), FONT_TEXT)

    # Сохраняем карточку
    background.save(output_path)
    print(f"Карточка сохранена: {output_path}")
