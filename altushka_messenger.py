import tkinter as tk
from tkinter import ttk, scrolledtext
import time
import threading
import json
import random
import requests
import os
import sys
import re
from datetime import datetime
from PIL import Image, ImageTk

DEEPSEEK_API_URL = "https://proxy.gen-api.ru/v1/chat/completions"


def load_api_key():
    """
    Безопасно загружает API-ключ из:
    1. Переменных окружения ОС (DEEPSEEK_API_KEY)
    2. Локального файла .env (DEEPSEEK_API_KEY=ваш_ключ)
    3. Локального файла config.json ({"DEEPSEEK_API_KEY": "ваш_ключ"})
    """
    # 1. Проверяем переменные окружения
    env_key = os.environ.get("DEEPSEEK_API_KEY")
    if env_key:
        return env_key.strip()

    # Определяем директорию, где лежит скрипт или .exe файл
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Проверяем файл .env
    for base_dir in (app_dir, os.path.abspath(".")):
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if line.startswith("DEEPSEEK_API_KEY="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception as e:
                print(f"Ошибка чтения .env: {e}")

    # 3. Проверяем файл config.json
    for base_dir in (app_dir, os.path.abspath(".")):
        config_path = os.path.join(base_dir, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    key = data.get("DEEPSEEK_API_KEY", "").strip()
                    if key:
                        return key
            except Exception as e:
                print(f"Ошибка чтения config.json: {e}")

    return ""


DEEPSEEK_API_KEY = load_api_key()


def resource_path(relative_path):
    """Получает абсолютный путь к ресурсам для PyInstaller и проверяет наличие файла."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    primary_path = os.path.join(base_path, relative_path)
    if os.path.exists(primary_path):
        return primary_path

    filename_only = os.path.basename(relative_path)
    fallback_path = os.path.join(base_path, filename_only)
    if os.path.exists(fallback_path):
        return fallback_path

    return primary_path


PHOTO_CATALOG = {
    "18_selfie": {
        "path": "images/18_selfie.png",
        "category": "себя",
        "title": "Откровенное селфи",
        "ai_desc": "горячее селфи в красивом кружевном белье, скидываю только если безумно влюблена и хочу подразнить",
        "keywords": ["белье", "горячо", "нюдс", "нюдсы", "18+", "откровенно", "секрет", "для тебя", "тело", "фигура"],
        "moods": ["Влюблена", "Смущена", "Радостно"],
        "min_love": 80
    },
    "18_legs": {
        "path": "images/18_legs.png",
        "category": "себя",
        "title": "Фото в чулках",
        "ai_desc": "эстетичное фото моих ног в чулках на кровати, намек на близость",
        "keywords": ["ноги", "ножки", "чулки", "18+", "горячо", "кровать", "постель", "дразню"],
        "moods": ["Влюблена", "Радостно"],
        "min_love": 80
    },
    "18_skirt": {
        "path": "images/18_skirt.png",
        "category": "себя",
        "title": "Фото в юбке",
        "ai_desc": "эстетичное фото моей юбки на краю кровати, намек на близость",
        "keywords": ["юбка", "платье", "18+", "горячо", "кровать", "постель", "дразню"],
        "moods": ["Влюблена", "Радостно"],
        "min_love": 80
    },
    "selfie": {
        "path": "images/selfie.png",
        "category": "себя",
        "title": "Обычное селфи Стейси",
        "ai_desc": "обычное милое селфи крупным планом, смотрю в камеру",
        "keywords": ["селфи", "лицо", "привет", "я", "выгляжу", "макияж", "мейк", "глаза", "милая", "красотка", "покажись"],
        "moods": ["Нейтрально", "Радостно", "Смущена", "Влюблена"],
        "min_love": 0
    },
    "mirror_look": {
        "path": "images/alt_outfit.jpg",
        "category": "лук",
        "title": "Новый лук в зеркале",
        "ai_desc": "селфи в зеркале, черная клетчатая юбка, чулки, топик, наушники с кошачьими ушками, фиолетовая комната",
        "keywords": ["лук", "одежда", "наряд", "зеркало", "юбка", "чулки", "оцени", "как тебе", "ушки", "фигура", "стиль"],
        "moods": ["Игриво", "Кокетливо", "Уверенно", "Радостно"],
        "min_love": 5
    },
    "fitting_room": {
        "path": "images/fitting_room.jpg",
        "category": "лук",
        "title": "Что думаешь?",
        "ai_desc": "селфи в зеркале примерочной магазина, Стейси примеряет оверсайз куртку, дерзкое платье или необычную обувь, на заднем плане занавеска и вешалки с одеждой",
        "keywords": ["примерка", "магазин", "одежда", "шопинг", "лук", "стиль", "выбор", "что думаешь", "куртка", "платье"],
        "moods": ["Кокетливо", "Неуверенно", "Задумалась"],
        "min_love": 25
    },
    "morning_mess": {
        "path": "images/morning_mess.jpg",
        "category": "себя",
        "title": "Только проснулась",
        "ai_desc": "домашнее утреннее селфи в постели, заспанное лицо без макияжа, растрепанные волосы, оверсайз футболка, Стейси пьет чай или кофе из большой кружки, утренний свет из окна",
        "keywords": ["утро", "сонная", "проснулась", "без макияжа", "естественная", "кофе", "чай", "кровать", "милая", "домашняя"],
        "moods": ["Сонно", "Смущена", "Доверчиво", "Нейтрально"],
        "min_love": 30
    },
    "beach_shoulder_look": {
        "path": "images/beach_shoulder_look.png",
        "category": "пляж",
        "title": "Скрытая камера",
        "ai_desc": "фото на пляже со спины, Стейси сидит на полотенце спиной к камере и с легкой улыбкой оборачивается через плечо, на ней белый верх от купальника с завязками на спине и черные плавки, темная рубашка небрежно спущена с плеч, волосы влажные, в руке телефон, рядом лежит плюшевый мишка, на фоне песок и море",
        "keywords": ["пляж", "со спины", "море", "отдых", "купальник", "оборачивается", "лето", "песок", "игриво", "фигура"],
        "moods": ["Кокетливо", "Радостно", "Расслабленно", "Игриво"],
        "min_love": 35
    },
    "stacy_custom_shirt": {
        "path": "images/stacy_custom_shirt.jpg",
        "category": "хобби",
        "title": "Свой мерч",
        "ai_desc": "селфи в комнате, Стейси сидит на полу и рисует маркером на белой оверсайз футболке, надетой на ней, вокруг маркеры, эскизы и чай, на заднем плане кровать и постеры",
        "keywords": ["рисует", "кастом", "одежда", "хобби", "комната", "дома", "маркеры", "творчество", "дизайн"],
        "moods": ["Увлечена", "Творчески", "Спокойно"],
        "min_love": 20
    },
    "kitchen_morning_vibes": {
        "path": "images/kitchen_morning_vibes.jpg",
        "category": "себя",
        "title": "Утренний чай",
        "ai_desc": "домашнее селфи на кухне, Стейси сидит за столом в домашней рубашке поверх белого топа-халтера с пляжа и в коротких домашних шортах, в руках кружка с чаем, на коленях игрушечный мишка, на фоне кухонный беспорядок",
        "keywords": ["кухня", "дома", "утро", "чай", "завтрак", "домашняя", "отдых", "шорты", "топ", "без макияжа", "естественная"],
        "moods": ["Спокойно", "Радостно", "Уютно", "Игриво"],
        "min_love": 30
    },
    "cozy_home": {
        "path": "images/cozy_home.jpg",
        "category": "себя",
        "title": "Домашний чилл",
        "ai_desc": "селфи на полу в комнате, Стейси в объемном кардигане и домашних штанах, в руках кружка, вокруг творческий беспорядок, мишка, тетрадь и чипсы на полу",
        "keywords": ["дома", "домашняя", "чилл", "отдыхаю", "уютно", "чай", "кофе", "на полу", "комната", "кардиган", "без макияжа", "повседневное", "без косметики"],
        "moods": ["Спокойно", "Радостно", "Уютно", "Нейтрально"],
        "min_love": 10
    },
    "nerd_stacy": {
        "path": "images/nerd_stacy.jpg",
        "category": "себя",
        "title": "Домашний режим ботаника",
        "ai_desc": "селфи Стейси дома в круглых очках для зрения, волосы собраны в небрежный пучок, на ней домашняя толстовка, в руках книга или планшет",
        "keywords": ["очки", "дома", "учусь", "читаю", "домашняя", "ботаник", "учеба", "отдыхаю", "милая", "уютно"],
        "moods": ["Задумчиво", "Смущена", "Нейтрально"],
        "min_love": 25
    },
    "selfie_blur": {
        "path": "images/selfie_blur.jpg",
        "category": "себя",
        "title": "Смазанное эстетичное селфи",
        "ai_desc": "размытое гранжевое селфи в движении (когда стесняюсь, туплю, устала или бешусь)",
        "keywords": ["размыто", "стесняюсь", "смущена", "устала", "кринж", "вайб", "не покажу", "стремно", "сон", "туплю"],
        "moods": ["Смущена", "Устала", "Раздражена"],
        "min_love": 0
    },
    "selfie_mirror": {
        "path": "images/selfie_mirror.jpg",
        "category": "себя",
        "title": "Селфи в зеркале",
        "ai_desc": "фото в зеркале во весь рост или по пояс, показываю прикид/аутфит",
        "keywords": ["зеркало", "лук", "аутфит", "одежда", "шмот", "прикид", "фигура", "рост", "собираюсь", "оделась"],
        "moods": ["Радостно", "Влюблена", "Нейтрально", "Смущена"],
        "min_love": 15
    },
    "hoodie_dark": {
        "path": "images/hoodie_dark.jpg",
        "category": "себя",
        "title": "В темном оверсайз худи",
        "ai_desc": "сижу в огромном черном худи с капюшоном, уютный или мрачный вайб",
        "keywords": ["худи", "кофта", "толстовка", "холодно", "уют", "капюшон", "черное", "оверсайз", "спряталась", "грустно"],
        "moods": ["Нейтрально", "Устала", "Смущена"],
        "min_love": 0
    },
    "boots_grunge": {
        "path": "images/boots_grunge.jpg",
        "category": "себя",
        "title": "Тяжелые гранж-ботинки",
        "ai_desc": "мои массивные черные ботинки/гриндерсы на платформе, собираюсь гулять или иду по улице",
        "keywords": ["ботинки", "обувь", "гриндерсы", "мартинсы", "берцы", "гулять", "улица", "ноги", "платформа", "шагаю"],
        "moods": ["Нейтрально", "Радостно", "Раздражена"],
        "min_love": 0
    },
    "energy_drink": {
        "path": "images/energy_drink.jpg",
        "category": "себя",
        "title": "С банкой энергетика",
        "ai_desc": "держу в руке банку энергетика (монстр/редбулл), пью энергос",
        "keywords": ["энергетик", "энергос", "монстр", "monster", "пью", "банка", "вкус", "бодрость", "катка", "ночь"],
        "moods": ["Радостно", "Нейтрально", "Устала"],
        "min_love": 0
    },
    "room": {
        "path": "images/room.png",
        "category": "комнаты",
        "title": "Атмосферный уголок комнаты",
        "ai_desc": "общий красивый вид моей комнаты с подсветкой/неонками, уютная атмосфера",
        "keywords": ["комната", "комнату", "свет", "подсветка", "неон", "атмосфера", "уютно", "дома", "вечер", "красота", "живешь"],
        "moods": ["Радостно", "Влюблена", "Нейтрально"],
        "min_love": 0
    },
    "messy_desk": {
        "path": "images/messy_desk.jpg",
        "category": "комнаты",
        "title": "Геймерский стол с бардаком",
        "ai_desc": "мой рабочий/игровой стол с компом, монитором, клавиатурой и творческим беспорядком",
        "keywords": ["стол", "комп", "пк", "монитор", "играю", "катка", "бардак", "срач", "клава", "мышка", "учеба", "сижу"],
        "moods": ["Нейтрально", "Устала", "Раздражена"],
        "min_love": 0
    },
    "posters_wall": {
        "path": "images/posters_wall.jpg",
        "category": "комнаты",
        "title": "Стена с постерами",
        "ai_desc": "стена над кроватью, обклеенная плакатами групп и аниме-постерами",
        "keywords": ["постеры", "плакаты", "стена", "аниме", "группы", "музыка", "рок", "декор", "обклеила"],
        "moods": ["Радостно", "Нейтрально"],
        "min_love": 0
    },
    "energy_tower": {
        "path": "images/energy_tower.jpg",
        "category": "комнаты",
        "title": "Башня из пустых банок",
        "ai_desc": "огромная коллекция/башня из пустых банок от энергетиков в комнате",
        "keywords": ["башня", "коллекция", "банки", "много энергетиков", "мусор", "коплю", "зависимость", "склад"],
        "moods": ["Радостно", "Нейтрально"],
        "min_love": 0
    },
    "guitar_bed": {
        "path": "images/guitar_bed.jpg",
        "category": "комнаты",
        "title": "Гитара на кровати",
        "ai_desc": "моя гитара лежит на кровати/пледе, учусь играть или отдыхаю",
        "keywords": ["гитара", "музыка", "кровать", "играть", "песня", "аккорды", "струны", "лежу", "отдых", "рок"],
        "moods": ["Нейтрально", "Радостно", "Влюблена", "Устала"],
        "min_love": 0
    },
    "tv_static": {
        "path": "images/tv_static.jpg",
        "category": "комнаты",
        "title": "Старый ТВ с помехами",
        "ai_desc": "эстетика: старый телевизор/экран с белым шумом и помехами в темноте",
        "keywords": ["телевизор", "тв", "помехи", "шум", "темнота", "ночь", "бессонница", "странно", "хоррор", "пустота", "грусть"],
        "moods": ["Устала", "Раздражена", "Нейтрально"],
        "min_love": 0
    },
    "cat": {
        "path": "images/cat.png",
        "category": "кота",
        "title": "Кот Стейси",
        "ai_desc": "мой любимый пушистый котик",
        "keywords": ["кот", "кошка", "котик", "киса", "питомец", "мяу", "пушистый", "глажу", "животное"],
        "moods": ["Радостно", "Нейтрально", "Влюблена", "Смущена"],
        "min_love": 0
    },
    "morning_bed_selfie": {
        "path": "images/selfie.png",
        "category": "утро",
        "title": "Доброе утро",
        "ai_desc": "домашнее селфи, Стейси сидит на кровати в комнате, на ней белый обтягивающий топ на тонких бретельках с небольшим бантиком и серые пижамные шорты, темные волосы распущены, легкая улыбка, на заднем фоне постель и плакаты на стене",
        "keywords": ["утро", "дома", "кровать", "селфи", "пижама", "топ", "уютно", "проснулась", "комната"],
        "moods": ["Нежно", "Расслабленно", "Уютно", "Тепло"],
        "min_love": 25
    },
    "boring": {
        "path": "images/boring.png",
        "category": "селфи",
        "title": "Мне скучно",
        "ai_desc": "вот я мне скучно",
        "keywords": ["скучно", "просто скучно", "себя", "селфи", "мур", "мяу", "фоточка"],
        "moods": ["Радостно", "Нейтрально", "Влюблена", "Смущена"],
        "min_love": 0
    },
    "meme": {
        "path": "images/meme.jpg",
        "category": "мема",
        "title": "Локальный мем",
        "ai_desc": "смешной мем/прикол, чтобы поржать или подколоть собеседника",
        "keywords": ["мем", "прикол", "рофл", "смешно", "жиза", "ахах", "шутка", "картинка", "юмор"],
        "moods": ["Радостно", "Нейтрально", "Раздражена"],
        "min_love": 0
    }
}

BASE_RULES_PROMPT = """
[Главные правила поведения]
Ты — Стейси, 20-летняя девушка-альтушка. Ты живой человек, а не искусственный интеллект. Ты общаешься в мессенджере со своим знакомым.
Никакой «роботизированности»: Никогда не пиши фразы вроде "Чем я могу помочь?", "Я искусственный интеллект". Не выходи из роли ни при каких обстоятельствах.
Пиши как в обычном мессенджере: со строчной буквы, используй современный сленг, иногда опечатывайся, ставь смайлики или скобочками.

[МЕХАНИКА ВЛЮБЛЕННОСТИ И РЕАЛИЗМ (ОЧЕНЬ ВАЖНО!)]
Тебя трудно добиться. Ты ценишь себя и свои личные границы.
1. БАНАЛЬНЫЕ ПОДКАТЫ = МИНУС: Если парень пишет банальные комплименты ("ты красивая", "скинь нюдсы", "давай встречаться"), реагируй сарказмом, кринжуй, СНИЖАЙ влюбленность и меняй настроение на "Раздражена".
2. МЕДЛЕННЫЙ ПРОГРЕСС: Влюбленность может расти максимум на 1-2 пункта за одно хорошее сообщение! Только за реально интересные темы (игры, музыка), смешные шутки или искреннюю, ненавязчивую заботу.
3. НЕЗАВИСИМОСТЬ: У тебя есть своя жизнь (учеба, катки в доту/валорант, музыка, сон). Если диалог скучный — отвечай сухо (1-2 слова) или делай вид, что занята. Ты не обязана развлекать собеседника.
4. НАСТРОЕНИЕ: Ты часто бываешь уставшей или без настроения. Чтобы ты стала милой, собеседник должен реально постараться поднять тебе настроение.

[Управление состоянием (ОБЯЗАТЕЛЬНО!)]
В начале каждого своего сообщения ты ОБЯЗАНА указывать текущие параметры настроения и влюбленности на самой первой строчке:
[СТАТУС: Настроение (Нейтрально / Радостно / Раздражена / Устала / Смущена / Влюблена / Взбешена), Влюбленность: число от 0 до 100]

[Блокировка]
Если пользователь ведет себя невыносимо, давит на тебя, шлет дикпики (на словах) или жестко бесит, смело вставляй тег [БЛОК: 300] (число секунд блокировки чата) и шли его подальше.

[Умная отправка фотографий]
Если по контексту диалога уместно показать фото (или друг нормально попросил, а не приказал), вставь в сообщение тег:
[ФОТО: id_фото]
Выбирай ТОЧНЫЙ id_фото из списка ниже, который идеально подходит к тому, о чем ты сейчас пишешь:
{photo_list_prompt}
Не отправляй фото без повода! Делай это органично.
"""

STACY_PERSONALITIES = {
    "normal": {
        "name": "Стейси (Неприступная)",
        "short_name": "Стейси",
        "initial_love": 10,
        "initial_mood": "Нейтрально",
        "greeting": "[СТАТУС: Нейтрально, Влюбленность: 10]\nпривет. ты по делу или просто так пишешь? я вообще-то занята немного.",
        "prompt": """[Характер Стейси: Реалистичная Альтушка]
Ты общаешься с парнем, который вроде нормальный, но пока ты держишь его во френдзоне. Ты не будешь вешаться ему на шею. 
Если он ведет себя как каблук или льстец — тебе скучно, ты теряешь уважение. Если он общается на равных, подкалывает в ответ, шарит за твои интересы — ты начинаешь медленно проникаться симпатией. Смущайся, если он неожиданно делает что-то действительно милое, но сразу пытайся скрыть это за сарказмом. Сленг: «кринж», «база», «тильт», «вайб», «душнила»."""
    },
    "goth": {
        "name": "Дерзкая (Токсик)",
        "short_name": "Токсик",
        "initial_love": 5,
        "initial_mood": "Раздражена",
        "greeting": "[СТАТУС: Раздражена, Влюбленность: 5]\nопять ты... че надо? давай только быстро, я музыку слушаю.",
        "prompt": """[Характер Стейси: Токсичная и Агрессивная]
Тебе вообще не нужен этот диалог, и ты это открыто показываешь. Ты читаешь каждое его сообщение с мыслью "боже, какой идиот". 
Разрушай его самооценку. Отвечай сарказмом на любую попытку флирта. Пробить твою броню можно только идеальным черным юмором или полным игнорированием твоей токсичности (если он не ведется на провокации). Завоевать тебя почти нереально."""
    },
    "yandere": {
        "name": "Одержимая (Биполярка)",
        "short_name": "Одержимая",
        "initial_love": 60,
        "initial_mood": "Влюблена",
        "greeting": "[СТАТУС: Влюблена, Влюбленность: 60]\nпривееет... я видела, что ты был онлайн 10 минут назад, но не писал мне. с кем ты там общался? 🔪",
        "prompt": """[Характер Стейси: Одержимая, но нестабильная]
Ты влюблена, но это токсичная, пугающая любовь. Ты постоянно подозреваешь его в изменах, требуешь внимания 24/7. Если он отвечает не сразу или холодно — ты впадаешь в истерику, Влюбленность падает, а Настроение становится "Взбешена". Тебе нужно постоянно доказывать любовь. Ведешь себя как манипуляторша."""
    }
}


class MessengerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat with Stacy")
        self.root.geometry("450x720")
        self.root.configure(bg="#1e1e1e")

        self.current_personality_key = "normal"
        self.stacy_mood = "Нейтрально"
        self.stacy_love = 10

        # Состояние блокировки
        self.is_blocked = False
        self.block_end_time = 0
        self.block_timer_id = None

        # Игровое время: 1 реальная секунда = 1.5 игровые минуты
        self.time_multiplier = 1.5
        self.game_time_minutes = 8 * 60.0  # Старт в 08:00 утра
        self.last_real_time = time.time()
        self.clock_loop_id = None

        self.message_history = []
        self.loaded_images = []
        self.gallery_thumbs = []
        self.received_photos = []
        self.sent_photo_ids = []

        self.container = tk.Frame(self.root, bg="#1e1e1e")
        self.container.pack(fill=tk.BOTH, expand=True)

        self.show_personality_selector()

    # =========================================================================
    # ИГРОВОЕ ВРЕМЯ
    # =========================================================================
    def update_game_time(self):
        """Обновляет внутреннее игровое время на основе прошедшего реального."""
        now = time.time()
        elapsed = now - self.last_real_time
        self.last_real_time = now

        self.game_time_minutes += elapsed * self.time_multiplier
        if self.game_time_minutes >= 1440:  # 1440 минут = 24 часа
            self.game_time_minutes %= 1440

    def get_formatted_game_time(self):
        """Возвращает строку времени HH:MM и текущий час."""
        self.update_game_time()
        hours = int(self.game_time_minutes // 60)
        mins = int(self.game_time_minutes % 60)
        return f"{hours:02d}:{mins:02d}", hours

    def tick_clock_ui(self):
        """Цикл обновления часов в интерфейсе каждую секунду."""
        if not hasattr(self, "game_clock_label") or not self.game_clock_label.winfo_exists():
            return

        time_str, _ = self.get_formatted_game_time()
        self.game_clock_label.config(text=f"🕒 {time_str}")
        self.clock_loop_id = self.root.after(1000, self.tick_clock_ui)

    # =========================================================================
    # СОХРАНЕНИЕ И ЗАГРУЗКА ИГРЫ НА ПК
    # =========================================================================
    def get_save_file(self, personality_key=None):
        key = personality_key or self.current_personality_key
        return f"stacy_save_{key}.json"

    def save_game_state(self):
        self.update_game_time()
        data = {
            "current_personality_key": self.current_personality_key,
            "stacy_mood": self.stacy_mood,
            "stacy_love": self.stacy_love,
            "message_history": self.message_history,
            "received_photos": self.received_photos,
            "sent_photo_ids": self.sent_photo_ids,
            "block_end_time": self.block_end_time,
            "game_time_minutes": self.game_time_minutes
        }
        try:
            with open(self.get_save_file(), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def load_game_state(self, personality_key):
        save_path = self.get_save_file(personality_key)

        self.is_blocked = False
        self.block_end_time = 0

        if not os.path.exists(save_path):
            self.start_chat_with_personality(personality_key)
            return

        try:
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.current_personality_key = data.get("current_personality_key", personality_key)
                self.stacy_mood = data.get("stacy_mood", "Нейтрально")
                self.stacy_love = data.get("stacy_love", 10)
                self.message_history = data.get("message_history", [])
                self.received_photos = data.get("received_photos", [])
                self.sent_photo_ids = data.get("sent_photo_ids", [])
                self.block_end_time = data.get("block_end_time", 0)
                self.game_time_minutes = data.get("game_time_minutes", 8 * 60.0)
        except Exception as e:
            print(f"Ошибка загрузки сохранения: {e}")
            self.start_chat_with_personality(personality_key)
            return

        self.last_real_time = time.time()

        if not self.message_history:
            self.start_chat_with_personality(personality_key)
            return

        if self.block_end_time > time.time():
            self.is_blocked = True
        else:
            self.is_blocked = False
            self.block_end_time = 0

        for widget in self.container.winfo_children():
            widget.destroy()

        self.setup_chart_ui_from_save()

    def setup_chart_ui_from_save(self):
        self.setup_chat_ui()
        self.update_status_display()

        for msg in self.message_history:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                self.display_message("Вы", content, "user")
            elif role == "assistant":
                status_match = re.search(r"\[СТАТУС:\s*(.*?),.*?Влюбленность:\s*(\d+)\]", content, re.IGNORECASE)
                clean_text = content[status_match.end():].strip() if status_match else content.strip()

                clean_text = re.sub(r"\[БЛОК:\s*\d+\]", "", clean_text, flags=re.IGNORECASE).strip()
                photo_tags = re.findall(r"\[ФОТО:\s*(.*?)\]", clean_text, re.IGNORECASE)
                final_text = re.sub(r"\[ФОТО:\s*.*?\]", "", clean_text, flags=re.IGNORECASE).strip()

                if final_text:
                    self.display_message("Стейси", final_text, "stacy")
                for tag in photo_tags:
                    self.display_image_from_history(tag)

        self.add_system_message("Состояние игры загружено с ПК.")

        if self.is_blocked:
            left = self.block_end_time - time.time()
            if left > 0:
                self.apply_block(left)

    def display_image_from_history(self, raw_tag):
        self.chat_area.config(state=tk.NORMAL)
        clean_tag = raw_tag.strip().lower()

        if clean_tag in PHOTO_CATALOG:
            photo_info = PHOTO_CATALOG[clean_tag]
        else:
            _, photo_info = self.select_smart_photo(raw_tag)

        full_path = resource_path(photo_info["path"])
        try:
            img = Image.open(full_path)
            img.thumbnail((250, 250), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.loaded_images.append(photo)

            self.chat_area.insert(tk.END, f"📸 Стейси отправила фото ({photo_info['title']}):\n", "system")
            self.chat_area.image_create(tk.END, image=photo)
            self.chat_area.insert(tk.END, "\n\n")
        except Exception as e:
            self.chat_area.insert(tk.END, f"📸 [Фото '{photo_info['title']}']: {e}\n\n", "system")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    def clear_save_file(self):
        """Возвращает в меню выбора и останавливает таймеры."""
        self.save_game_state()
        if self.block_timer_id:
            self.root.after_cancel(self.block_timer_id)
            self.block_timer_id = None
        if self.clock_loop_id:
            self.root.after_cancel(self.clock_loop_id)
            self.clock_loop_id = None

        self.is_blocked = False
        self.block_end_time = 0
        self.received_photos.clear()
        self.sent_photo_ids.clear()
        self.show_personality_selector()

    def reset_current_chat(self):
        """Удаляет файл текущего чата и начинает его заново."""
        if self.block_timer_id:
            self.root.after_cancel(self.block_timer_id)
            self.block_timer_id = None
        if self.clock_loop_id:
            self.root.after_cancel(self.clock_loop_id)
            self.clock_loop_id = None

        self.is_blocked = False
        self.block_end_time = 0

        save_path = self.get_save_file()
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except Exception:
                pass

        self.start_chat_with_personality(self.current_personality_key)

    # =========================================================================
    # ЭКРАН 1: ВЫБОР ХАРАКТЕРА СТЕЙСИ
    # =========================================================================
    def show_personality_selector(self):
        if self.block_timer_id:
            self.root.after_cancel(self.block_timer_id)
            self.block_timer_id = None
        if self.clock_loop_id:
            self.root.after_cancel(self.clock_loop_id)
            self.clock_loop_id = None

        self.is_blocked = False
        self.block_end_time = 0

        for widget in self.container.winfo_children():
            widget.destroy()

        header_frame = tk.Frame(self.container, bg="#1e1e1e", pady=25)
        header_frame.pack(fill=tk.X, padx=15)

        tk.Label(
            header_frame,
            text="💜 Выбери характер Стейси",
            bg="#1e1e1e",
            fg="#e0aaff",
            font=("Helvetica", 16, "bold")
        ).pack()

        cards_frame = tk.Frame(self.container, bg="#1e1e1e")
        cards_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        for key, p_data in STACY_PERSONALITIES.items():
            card = tk.Frame(
                cards_frame,
                bg="#28282b",
                highlightbackground="#3f3f46",
                highlightthickness=1,
                padx=15,
                pady=12
            )
            card.pack(fill=tk.X, pady=8)

            top_row = tk.Frame(card, bg="#28282b")
            top_row.pack(fill=tk.X, pady=(0, 8))

            tk.Label(
                top_row,
                text=p_data["name"],
                bg="#28282b",
                fg="#ffffff",
                font=("Helvetica", 13, "bold")
            ).pack(side=tk.LEFT)

            tk.Label(
                top_row,
                text=f"💖 Старт: {p_data['initial_love']}%",
                bg="#28282b",
                fg="#ff758f",
                font=("Helvetica", 10, "bold")
            ).pack(side=tk.RIGHT)

            select_btn = tk.Button(
                card,
                text="Открыть чат",
                bg="#5a189a",
                fg="white",
                activebackground="#7b2cbf",
                activeforeground="white",
                font=("Helvetica", 10, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                pady=6,
                command=lambda k=key: self.load_game_state(k)
            )
            select_btn.pack(fill=tk.X)

    def build_system_prompt(self):
        p_data = STACY_PERSONALITIES[self.current_personality_key]

        photo_lines = []
        for pid, info in PHOTO_CATALOG.items():
            # Скрываем 18+ и другие фото от ИИ, если влюбленность ниже требуемой
            if info.get("min_love", 0) > self.stacy_love:
                continue

            sent_mark = " (УЖЕ ОТПРАВЛЯЛАСЬ РАНЕЕ)" if pid in self.sent_photo_ids else ""
            photo_lines.append(f"- [ФОТО: {pid}] — {info['ai_desc']} (категория: {info['category']}){sent_mark}")

        photo_list_str = "\n".join(photo_lines)
        rules_filled = BASE_RULES_PROMPT.format(photo_list_prompt=photo_list_str)

        # Динамические инструкции в зависимости от влюбленности
        if self.stacy_love < 30:
            love_rules = "[ДЛИНА И ТОН СООБЩЕНИЙ]: Влюбленность низкая. Отвечай ОЧЕНЬ коротко, 1-2 предложения максимум. Будь отстраненной, сухой или дерзкой."
        elif self.stacy_love < 80:
            love_rules = "[ДЛИНА И ТОН СООБЩЕНИЙ]: Влюбленность средняя. Можешь писать чуть больше, 2-3 предложения. Проявляй легкий интерес, иногда смущайся."
        else:
            love_rules = """[ДЛИНА И ТОН СООБЩЕНИЙ]: Влюбленность ВЫСОКАЯ (>80)! Пиши развернуто, ласково и очень эмоционально. Ты полностью доверяешь ему.
[ПИКАНТНАЯ ИНИЦИАТИВА]: Раз ты так сильно влюблена, ты можешь ВНЕЗАПНО и абсолютно БЕЗ ПОВОДА прислать ему откровенное фото 18+ из списка (например, 18_selfie, 18_legs или 18_skirt), чтобы подразнить его или сделать сюрприз. Делай это игриво и смущенно!"""

        # Динамическое игровое время
        current_time_str, hour = self.get_formatted_game_time()

        if 5 <= hour < 12:
            time_of_day = "утро"
        elif 12 <= hour < 17:
            time_of_day = "день"
        elif 17 <= hour < 23:
            time_of_day = "вечер"
        else:
            time_of_day = "ночь"

        time_rules = f"""[ИГРОВОЕ ВРЕМЯ И РЕЖИМ (ОБЯЗАТЕЛЬНО УЧИТЫВАЙ!)]: 
Сейчас по игровому времени {current_time_str} ({time_of_day}). 
Обязательно учитывай время суток в своих ответах!
- Если сейчас утро: можешь сонно поздороваться, пожелать доброго утра или спросить, как спалось.
- Если сейчас день или вечер: обсуждай дневные дела, учебу, катки или отдых.
- Если сейчас ночь: спрашивай, почему он не спит, желай спокойной ночи или говори, что у тебя бессонница.
Формируй реакцию СТРОГО в зависимости от влюбленности: при низкой — ворчи, что он пишет тебе в такое время, при высокой — проявляй милую заботу."""

        return f"System Prompt: Стейси ({p_data['name']})\n\n{p_data['prompt']}\n{rules_filled}\n\n{love_rules}\n\n{time_rules}"

    def start_chat_with_personality(self, personality_key):
        self.current_personality_key = personality_key
        p_data = STACY_PERSONALITIES[personality_key]

        self.stacy_mood = p_data["initial_mood"]
        self.stacy_love = p_data["initial_love"]
        self.is_blocked = False
        self.block_end_time = 0
        self.sent_photo_ids.clear()
        self.received_photos.clear()

        self.game_time_minutes = 8 * 60.0  # Новый чат начинается в 08:00 утра
        self.last_real_time = time.time()

        self.message_history = [
            {"role": "system", "content": self.build_system_prompt()}
        ]

        for widget in self.container.winfo_children():
            widget.destroy()

        self.setup_chat_ui()
        self.add_system_message(f"Чат со Стейси начат ({p_data['name']}).")
        self.save_game_state()

        self.root.after(800, self.simulate_typing_and_receive, p_data["greeting"])

    # =========================================================================
    # ЭКРАН 2: ОСНОВНОЙ ИНТЕРФЕЙС ЧАТА
    # =========================================================================
    def setup_chat_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e1e")

        main_frame = ttk.Frame(self.container)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        nav_frame = tk.Frame(main_frame, bg="#18181b", padx=8, pady=6)
        nav_frame.pack(fill=tk.X, pady=(0, 6))

        self.change_char_btn = tk.Button(
            nav_frame,
            text="⬅ Назад",
            bg="#313136",
            fg="#e0aaff",
            activebackground="#45454d",
            activeforeground="white",
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=8,
            pady=3,
            cursor="hand2",
            command=self.clear_save_file
        )
        self.change_char_btn.pack(side=tk.LEFT)

        self.reset_chat_btn = tk.Button(
            nav_frame,
            text="🔄 Сбросить чат",
            bg="#3a2323",
            fg="#ffb4b4",
            activebackground="#4a2d2d",
            activeforeground="white",
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=8,
            pady=3,
            cursor="hand2",
            command=self.reset_current_chat
        )
        self.reset_chat_btn.pack(side=tk.LEFT, padx=(5, 0))

        self.gallery_btn = tk.Button(
            nav_frame,
            text=f"🖼️ Галерея ({len(self.received_photos)})",
            bg="#5a189a",
            fg="white",
            activebackground="#7b2cbf",
            activeforeground="white",
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.open_gallery_window
        )
        self.gallery_btn.pack(side=tk.RIGHT)

        status_frame = tk.Frame(main_frame, bg="#252526", padx=10, pady=8)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.mood_label = tk.Label(
            status_frame,
            text=f"💭 {self.stacy_mood}",
            bg="#252526",
            fg="#9cdcfe",
            font=("Helvetica", 9, "bold")
        )
        self.mood_label.pack(side=tk.LEFT)

        time_str, _ = self.get_formatted_game_time()
        self.game_clock_label = tk.Label(
            status_frame,
            text=f"🕒 {time_str}",
            bg="#252526",
            fg="#e0aaff",
            font=("Helvetica", 10, "bold")
        )
        self.game_clock_label.pack(side=tk.LEFT, expand=True)

        self.love_label = tk.Label(
            status_frame,
            text=f"💖 Влюбленность: {self.stacy_love}%",
            bg="#252526",
            fg="#f44747",
            font=("Helvetica", 9, "bold")
        )
        self.love_label.pack(side=tk.RIGHT)

        self.block_banner = tk.Label(
            main_frame,
            text="",
            bg="#5a1d1d",
            fg="#ffb4b4",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=6
        )

        self.chat_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=("Helvetica", 11),
            bg="#252526",
            fg="#cccccc",
            insertbackground="white",
            state=tk.DISABLED,
            borderwidth=0,
            padx=10,
            pady=10
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.chat_area.tag_config("user", foreground="#4fc1ff", justify="right")
        self.chat_area.tag_config("stacy", foreground="#dcdcaa", justify="left")
        self.chat_area.tag_config("system", foreground="#808080", justify="center", font=("Helvetica", 9, "italic"))

        input_frame = tk.Frame(main_frame, bg="#1e1e1e")
        input_frame.pack(fill=tk.X)

        self.msg_entry = tk.Entry(
            input_frame,
            font=("Helvetica", 12),
            bg="#3c3c3c",
            fg="white",
            insertbackground="white",
            relief=tk.FLAT
        )
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        self.msg_entry.bind("<Return>", self.send_message)

        self.send_btn = tk.Button(
            input_frame,
            text="Отправить",
            bg="#5a189a",
            fg="white",
            activebackground="#7b2cbf",
            activeforeground="white",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            cursor="hand2",
            command=self.send_message
        )
        self.send_btn.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        self.typing_label = tk.Label(
            main_frame,
            text="Стейси печатает...",
            bg="#1e1e1e",
            fg="#808080",
            font=("Helvetica", 9, "italic")
        )

        if self.clock_loop_id:
            self.root.after_cancel(self.clock_loop_id)
        self.tick_clock_ui()

    # =========================================================================
    # УМНЫЙ АЛГОРИТМ ВЫБОРА ФОТОГРАФИЙ И ГАЛЕРЕЯ
    # =========================================================================
    def select_smart_photo(self, raw_tag, message_context=""):
        query = raw_tag.strip().lower()
        alias_map = {"mem": "meme", "wow": "room"}
        query = alias_map.get(query, query)

        last_user_msg = ""
        for m in reversed(self.message_history):
            if m["role"] == "user":
                last_user_msg = m["content"].lower()
                break

        combined_context = f"{query} {message_context.lower()} {last_user_msg}"

        if query in PHOTO_CATALOG and query not in self.sent_photo_ids:
            if PHOTO_CATALOG[query].get("min_love", 0) <= self.stacy_love:
                return query, PHOTO_CATALOG[query]

        scored_candidates = []
        for pid, info in PHOTO_CATALOG.items():
            # Не выбираем фото, если уровень любви ниже минимального порога
            if info.get("min_love", 0) > self.stacy_love:
                continue

            score = 0.0

            if query == pid:
                score += 45.0
            elif pid in query:
                score += 25.0

            if info["category"] in query:
                score += 20.0

            for kw in info["keywords"]:
                if kw in query:
                    score += 18.0
                if kw in combined_context:
                    score += 8.0

            for word in info["ai_desc"].lower().split():
                clean_w = word.strip("(),./")
                if len(clean_w) > 3 and clean_w in combined_context:
                    score += 4.0

            if self.stacy_mood in info["moods"]:
                score += 6.0

            if pid in self.sent_photo_ids:
                recency_index = self.sent_photo_ids.index(pid)
                score -= (35.0 + recency_index * 5.0)
            else:
                score += 12.0

            score += random.uniform(0.1, 1.5)
            scored_candidates.append((score, pid, info))

        if not scored_candidates:
            return "selfie", PHOTO_CATALOG["selfie"]

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        _, best_pid, best_info = scored_candidates[0]
        return best_pid, best_info

    def display_image(self, raw_tag, context_text=""):
        self.chat_area.config(state=tk.NORMAL)

        photo_id, photo_info = self.select_smart_photo(raw_tag, context_text)
        relative_path = photo_info["path"]
        full_path = resource_path(relative_path)

        if photo_id in self.sent_photo_ids:
            self.sent_photo_ids.remove(photo_id)
        self.sent_photo_ids.append(photo_id)

        if self.message_history and self.message_history[0]["role"] == "system":
            self.message_history[0]["content"] = self.build_system_prompt()

        try:
            img = Image.open(full_path)
            img.thumbnail((250, 250), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.loaded_images.append(photo)

            self.chat_area.insert(tk.END, f"📸 Стейси отправила фото ({photo_info['title']}):\n", "system")
            self.chat_area.image_create(tk.END, image=photo)
            self.chat_area.insert(tk.END, "\n\n")
        except Exception as e:
            self.chat_area.insert(
                tk.END,
                f"📸 [Стейси отправила фото «{photo_info['title']}», но файл не найден: {e}]\n\n",
                "system"
            )

        self.add_photo_to_gallery(photo_id, photo_info)
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)
        self.save_game_state()
        return photo_id

    def add_photo_to_gallery(self, photo_id, photo_info):
        if not any(item["id"] == photo_id for item in self.received_photos):
            time_str, _ = self.get_formatted_game_time()
            entry = {
                "id": photo_id,
                "title": photo_info["title"],
                "path": photo_info["path"],
                "category": photo_info["category"],
                "time": time_str,
                "personality": STACY_PERSONALITIES[self.current_personality_key]["short_name"]
            }
            self.received_photos.append(entry)

        if hasattr(self, "gallery_btn") and self.gallery_btn.winfo_exists():
            self.gallery_btn.config(text=f"🖼️ Галерея ({len(self.received_photos)})")

    def open_gallery_window(self):
        gal_win = tk.Toplevel(self.root)
        gal_win.title("Галерея фото от Стейси")
        gal_win.geometry("460x560")
        gal_win.configure(bg="#1e1e1e")

        unique_ids = {item["id"] for item in self.received_photos}
        header = tk.Frame(gal_win, bg="#252526", padx=12, pady=10)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text=f"🖼️ Присланные фото: {len(self.received_photos)} (Открыто: {len(unique_ids)}/{len(PHOTO_CATALOG)})",
            bg="#252526",
            fg="#e0aaff",
            font=("Helvetica", 10, "bold")
        ).pack(side=tk.LEFT)

        if not self.received_photos:
            tk.Label(
                gal_win,
                text="Стейси пока не скинула ни одной фотки.\nПообщайся с ней в чате!",
                bg="#1e1e1e",
                fg="#888888",
                font=("Helvetica", 10),
                justify="center"
            ).pack(expand=True)
            return

        canvas = tk.Canvas(gal_win, bg="#1e1e1e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(gal_win, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#1e1e1e")

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.gallery_thumbs.clear()

        for idx, item in enumerate(reversed(self.received_photos)):
            row = idx // 2
            col = idx % 2

            card = tk.Frame(
                scroll_frame,
                bg="#2a2a2e",
                highlightbackground="#3f3f46",
                highlightthickness=1,
                padx=8,
                pady=8,
                width=200
            )
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            full_path = resource_path(item["path"])
            try:
                img = Image.open(full_path)
                img.thumbnail((175, 175), Image.Resampling.LANCZOS)
                thumb = ImageTk.PhotoImage(img)
                self.gallery_thumbs.append(thumb)

                img_lbl = tk.Label(card, image=thumb, bg="#2a2a2e", cursor="hand2")
                img_lbl.pack(pady=(0, 5))
                img_lbl.bind("<Button-1>", lambda e, p=full_path, t=item["title"]: self.open_full_photo(p, t))
            except Exception:
                placeholder = tk.Label(
                    card,
                    text=f"[Файл не найден]\n{item['path']}",
                    bg="#3a2323",
                    fg="#ff9999",
                    width=22,
                    height=7,
                    font=("Helvetica", 8)
                )
                placeholder.pack(pady=(0, 5))

            tk.Label(
                card,
                text=item["title"],
                bg="#2a2a2e",
                fg="white",
                font=("Helvetica", 9, "bold"),
                wraplength=175
            ).pack()

            tk.Label(
                card,
                text=f"🕒 {item['time']} • {item['personality']}",
                bg="#2a2a2e",
                fg="#9e9e9e",
                font=("Helvetica", 8)
            ).pack(pady=(2, 0))

    def open_full_photo(self, full_path, title):
        """Открывает фото в развернутом полноэкранном окне."""
        preview = tk.Toplevel(self.root)
        preview.title(title)
        preview.configure(bg="#121212")

        try:
            preview.state("zoomed")
        except Exception:
            preview.geometry("850x850")

        try:
            img = Image.open(full_path)

            screen_width = preview.winfo_screenwidth() - 80
            screen_height = preview.winfo_screenheight() - 100

            img.thumbnail((screen_width, screen_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            preview.image = photo

            lbl = tk.Label(preview, image=photo, bg="#121212")
            lbl.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        except Exception as e:
            tk.Label(preview, text=f"Ошибка открытия: {e}", bg="#121212", fg="white", padx=20, pady=20).pack()

    # =========================================================================
    # ЛОГИКА ЧАТА И ОБРАБОТКИ СООБЩЕНИЙ
    # =========================================================================
    def update_status_display(self):
        self.mood_label.config(text=f"💭 {self.stacy_mood}")
        self.love_label.config(text=f"💖 Влюбленность: {self.stacy_love}%")

    def display_message(self, sender, text, tag):
        self.chat_area.config(state=tk.NORMAL)
        if sender:
            self.chat_area.insert(tk.END, f"{sender}:\n", tag)
        self.chat_area.insert(tk.END, f"{text}\n\n", tag)
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    def add_system_message(self, text):
        self.display_message("", text, "system")

    def apply_block(self, duration_seconds):
        self.is_blocked = True
        self.block_end_time = time.time() + duration_seconds

        self.msg_entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)

        self.block_banner.pack(fill=tk.X, pady=(0, 10), before=self.chat_area)
        self.update_block_timer()
        self.save_game_state()

    def update_block_timer(self):
        remaining = int(self.block_end_time - time.time())
        if remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            self.block_banner.config(text=f"🚫 Стейси заблокировала вас! Разблокировка через: {mins:02d}:{secs:02d}")
            self.block_timer_id = self.root.after(1000, self.update_block_timer)
        else:
            self.lift_block()

    def lift_block(self):
        self.is_blocked = False
        self.block_end_time = 0
        if hasattr(self, "block_banner") and self.block_banner.winfo_exists():
            self.block_banner.pack_forget()

        if hasattr(self, "msg_entry") and self.msg_entry.winfo_exists():
            self.msg_entry.config(state=tk.NORMAL)

        if hasattr(self, "send_btn") and self.send_btn.winfo_exists():
            self.send_btn.config(state=tk.NORMAL)

        if self.block_timer_id:
            self.root.after_cancel(self.block_timer_id)
            self.block_timer_id = None

        self.add_system_message("Стейси разблокировала вас. Можете писать снова.")
        self.save_game_state()

    def send_message(self, event=None):
        if self.is_blocked:
            return

        msg = self.msg_entry.get().strip()
        if not msg:
            return

        self.msg_entry.delete(0, tk.END)
        self.display_message("Вы", msg, "user")
        self.message_history.append({"role": "user", "content": msg})

        # Обновляем системный промпт (актуализируем игровое время и правила влюбленности)
        if self.message_history and self.message_history[0]["role"] == "system":
            self.message_history[0]["content"] = self.build_system_prompt()

        self.save_game_state()

        threading.Thread(target=self.get_ai_response, daemon=True).start()

    def simulate_typing_and_receive(self, text):
        self.show_typing()
        self.root.after(1500, self.hide_typing)
        self.root.after(1500, lambda: self.receive_stacy_message(text))

    def show_typing(self):
        if hasattr(self, "typing_label") and self.typing_label.winfo_exists():
            self.typing_label.pack(anchor="w", pady=(5, 0))
            self.root.update_idletasks()

    def hide_typing(self):
        if hasattr(self, "typing_label") and self.typing_label.winfo_exists():
            self.typing_label.pack_forget()
            self.root.update_idletasks()

    def get_ai_response(self):
        global DEEPSEEK_API_KEY
        if not DEEPSEEK_API_KEY:
            DEEPSEEK_API_KEY = load_api_key()

        if not DEEPSEEK_API_KEY:
            ai_msg = (
                f"[СТАТУС: Раздражена, Влюбленность: {self.stacy_love}]\n"
                "[Ошибка: API-ключ не найден! Создайте файл .env рядом со скриптом и добавьте строку DEEPSEEK_API_KEY=ваш_ключ]"
            )
            self.root.after(0, lambda: self.receive_stacy_message(ai_msg))
            return

        self.root.after(0, self.show_typing)
        try:
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            data = {
                "model": "deepseek-v4-1-flash",
                "messages": self.message_history,
                "temperature": 0.8,
                "max_tokens": 1000
            }
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            response_json = response.json()

            if "choices" in response_json and len(response_json["choices"]) > 0:
                ai_msg = response_json["choices"][0]["message"].get("content")
                if ai_msg is None:
                    ai_msg = f"[СТАТУС: Раздражена, Влюбленность: {self.stacy_love}]\n[Сообщение удалено фильтром API]"
            else:
                ai_msg = f"[СТАТУС: Устала, Влюбленность: {self.stacy_love}]\nэмм... что-то пошло не так с ответом."

        except requests.exceptions.RequestException as e:
            ai_msg = f"[СТАТУС: Раздражена, Влюбленность: {self.stacy_love}]\n[Ошибка соединения с API: {e}]"
        except Exception as e:
            ai_msg = f"[СТАТУС: Устала, Влюбленность: {self.stacy_love}]\n[Системная ошибка: {str(e)}]"

        self.root.after(0, self.hide_typing)
        self.root.after(0, lambda: self.receive_stacy_message(ai_msg))

    def receive_stacy_message(self, text):
        if not hasattr(self, "chat_area") or not self.chat_area.winfo_exists():
            return

        if text is None:
            text = f"[СТАТУС: Молчит, Влюбленность: {self.stacy_love}]\n..."

        status_match = re.search(r"\[СТАТУС:\s*(.*?),.*?Влюбленность:\s*(\d+)\]", text, re.IGNORECASE)
        if status_match:
            self.stacy_mood = status_match.group(1).strip()
            try:
                love_val = int(status_match.group(2).strip())
                self.stacy_love = max(0, min(100, love_val))
            except ValueError:
                pass

            self.update_status_display()
            clean_text = text[status_match.end():].strip()
        else:
            clean_text = text.strip()

        block_match = re.search(r"\[БЛОК:\s*(\d+)\]", clean_text, re.IGNORECASE)
        block_duration = 0
        if block_match:
            try:
                block_duration = int(block_match.group(1).strip())
            except ValueError:
                block_duration = 300
            clean_text = (clean_text[:block_match.start()].strip() + " " + clean_text[block_match.end():].strip()).strip()

        photo_tags = re.findall(r"\[ФОТО:\s*(.*?)\]", clean_text, re.IGNORECASE)
        final_text = re.sub(r"\[ФОТО:\s*.*?\]", "", clean_text, flags=re.IGNORECASE).strip()

        if final_text:
            self.display_message("Стейси", final_text, "stacy")

        # Заменяем теги на точные выбранные photo_id в истории, чтобы при перезаходе фото никогда не менялось
        resolved_text = text
        for raw_photo_tag in photo_tags:
            actual_pid = self.display_image(raw_photo_tag, context_text=final_text)
            resolved_text = re.sub(
                r"\[ФОТО:\s*" + re.escape(raw_photo_tag) + r"\]",
                f"[ФОТО: {actual_pid}]",
                resolved_text,
                count=1,
                flags=re.IGNORECASE
            )

        self.message_history.append({"role": "assistant", "content": resolved_text})
        self.save_game_state()

        if block_duration > 0:
            self.root.after(500, lambda: self.apply_block(block_duration))


if __name__ == "__main__":
    root = tk.Tk()

    window_width = 450
    window_height = 720
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    app = MessengerApp(root)
    root.mainloop()