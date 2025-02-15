from PIL import Image, ImageDraw, ImageFont
import textwrap

# Пути к файлам
BACKGROUND_PATH = "background.jpg"  # Фон карточки
DEFAULT_PHOTO_PATH = "default_photo.jpg"  # Заглушка для фото

# Шрифты
FONT_TITLE = ImageFont.truetype("arial.ttf", 40)
FONT_SUBTITLE = ImageFont.truetype("arial.ttf", 25)
FONT_TEXT = ImageFont.truetype("arial.ttf", 22)

# Максимальная ширина текста (в пикселях)
TEXT_WIDTH = 900  # Подбери под свой макет


def wrap_text(draw, text, font, max_width):
    """Функция для автоматического переноса строк"""
    lines = []
    for line in text.split("\n"):
        wrapped_lines = textwrap.wrap(line, width=40)  # Количество символов в строке
        lines.extend(wrapped_lines)
    return lines


def draw_wrapped_text(draw, text, position, font, fill="black", max_width=TEXT_WIDTH):
    """Рисует текст с автоматическим переносом строк"""
    x, y = position
    lines = wrap_text(draw, text, font, max_width)
    for line in lines:
        draw.text((x, y), line, fill=fill, font=font)
        y += font.size + 5  # Интервал между строками
    return y  # Возвращает новую позицию Y


def generate_memorial_card(data, output_path):
    # Открываем фон
    background = Image.open(BACKGROUND_PATH).convert("RGB")
    draw = ImageDraw.Draw(background)
    width, height = background.size

    # Загружаем фото или используем заглушку
    try:
        photo = Image.open(data.get("photo_path", DEFAULT_PHOTO_PATH)).convert("RGB").resize((250, 300))
    except:
        photo = Image.open(DEFAULT_PHOTO_PATH).convert("RGB").resize((250, 300))

    # Рисуем ФИО
    title_x = width // 2 - draw.textbbox((0, 0), data["full_name"], font=FONT_TITLE)[2] // 2
    draw.text((title_x, 30), data["full_name"], fill="black", font=FONT_TITLE)

    # Рисуем даты
    date_text = f"{data['birth_date']} – {data['death_date']}"
    date_x = width // 2 - draw.textbbox((0, 0), date_text, font=FONT_SUBTITLE)[2] // 2
    draw.text((date_x, 80), date_text, fill="black", font=FONT_SUBTITLE)

    # Центрируем фото
    photo_x = width // 2 - photo.width // 2
    background.paste(photo, (photo_x, 130))

    # Начальная координата для текста
    text_x = 50
    text_y = 450

    # Рисуем текст с переносом строк
    text_y = draw_wrapped_text(draw, f"Описание: {data['description']}", (text_x, text_y), FONT_TEXT)
    text_y = draw_wrapped_text(draw, f"Место захоронения: {data['burial_place']}", (text_x, text_y), FONT_TEXT)
    text_y = draw_wrapped_text(draw, f"Награды: {', '.join(data['awards'])}", (text_x, text_y), FONT_TEXT)
    text_y = draw_wrapped_text(draw, f"Участие в военных событиях: {data['military_service']}", (text_x, text_y), FONT_TEXT)

    # Сохраняем карточку
    background.save(output_path)
    print(f"Карточка сохранена: {output_path}")


# Пример данных
data = {
    "full_name": "Карнаух Валерий Петрович",
    "birth_date": "21.06.1963",
    "death_date": "24.11.2023",
    "photo_path": "photo.jpg",  # Путь к фото (если есть)
    "description": "Герой военной операции, посвятивший свою жизнь защите Отечества. Участвовал в боевых действиях, проявил мужество и героизм.",
    "burial_place": "Село Раннее",
    "awards": ["Орден Мужества", "Медаль за Отвагу", "Орден Красной Звезды"],
    "military_service": "Участник спецоперации, принимал участие в оборонительных боях."
}

# Генерация карточки
generate_memorial_card(data, "output_card.png")
