import os
import telebot
from telebot import types
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BRAWL_API_KEY = os.getenv("BRAWL_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
headers = {"Authorization": f"Bearer {BRAWL_API_KEY}"}
user_tags = {}

# --- Старт ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Привет! Введи свой Player Tag (например: #2ABC123)")
    
# --- Сохраняем Player Tag ---
@bot.message_handler(func=lambda message: message.text.startswith("#"))
def save_tag(message):
    tag = message.text.strip().replace("#", "").upper()
    user_tags[message.chat.id] = tag
    bot.send_message(message.chat.id, f"✅ Твой Player Tag сохранён: #{tag}")
    show_menu(message.chat.id)

# --- Показываем меню с Inline кнопками ---
def show_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Текущие кубки", callback_data="current_trophies"))
    markup.add(types.InlineKeyboardButton("Лучший боец", callback_data="best_brawler"))
    markup.add(types.InlineKeyboardButton("Топ игроков в стране", callback_data="top_country"))
    markup.add(types.InlineKeyboardButton("Топ игроков в мире", callback_data="top_global"))
    bot.send_message(chat_id, "Выбери действие:", reply_markup=markup)

# --- Обработка нажатий на кнопки ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id

    if chat_id not in user_tags:
        bot.send_message(chat_id, "❌ Сначала отправь свой Player Tag (например: #2ABC123)")
        return

    tag = user_tags[chat_id]

    # --- Текущие кубки ---
    if call.data == "current_trophies":
        url = f"https://api.brawlstars.com/v1/players/%23{tag}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            bot.send_message(chat_id, "❌ Игрок не найден.")
            return
        data = response.json()
        bot.send_message(chat_id, f"🏆 Текущие кубки: {data['trophies']}")

    # --- Лучший боец ---
    elif call.data == "best_brawler":
        url = f"https://api.brawlstars.com/v1/players/%23{tag}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            bot.send_message(chat_id, "❌ Игрок не найден.")
            return
        data = response.json()
        best_brawler = max(data["brawlers"], key=lambda b: b["trophies"])
        bot.send_message(chat_id,
                         f"👑 Лучший боец: {best_brawler['name']}\n"
                         f"🏆 Кубки на нём: {best_brawler['trophies']}")

    # --- Топ игроков в стране ---
    elif call.data == "top_country":
        markup = types.InlineKeyboardMarkup()
        # Добавляем самые популярные страны, можно расширить список
        for code in ["UA", "US", "RU", "GB", "FR", "DE"]:
            markup.add(types.InlineKeyboardButton(code, callback_data=f"country_{code}"))
        bot.send_message(chat_id, "Выбери страну:", reply_markup=markup)

    # --- Топ игроков в мире ---
    elif call.data == "top_global":
        url = "https://api.brawlstars.com/v1/rankings/players"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            bot.send_message(chat_id, "❌ Ошибка получения глобального топа.")
            return
        data = response.json()
        text = "🌎 Топ игроков в мире:\n"
        for i, player in enumerate(data["items"][:10], 1):
            text += f"{i}. {player['name']} — {player['trophies']} кубков\n"
        bot.send_message(chat_id, text)

    # --- Топ по выбранной стране ---
    elif call.data.startswith("country_"):
        country_code = call.data.split("_")[1]
        url = f"https://api.brawlstars.com/v1/rankings/players/country/{country_code}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            bot.send_message(chat_id, "❌ Страна не найдена или нет данных.")
            return
        data = response.json()
        text = f"🏅 Топ игроков в {country_code}:\n"
        for i, player in enumerate(data["items"][:10], 1):
            text += f"{i}. {player['name']} — {player['trophies']} кубков\n"
        bot.send_message(chat_id, text)

    # Показываем меню снова после каждого действия
    show_menu(chat_id)

print("Бот запущен...")
bot.polling()
