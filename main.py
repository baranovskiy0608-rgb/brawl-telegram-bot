import os
import telebot
from telebot import types
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BRAWL_API_KEY = os.getenv("BRAWL_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
headers = {"Authorization": f"Bearer {BRAWL_API_KEY}"}
user_tags = {}

# --- Стартовое сообщение с меню ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Текущие кубки", "Лучший боец")
    markup.add("Топ игроков в стране", "Топ игроков в мире")
    
    bot.send_message(message.chat.id,
                     "👋 Привет! Введи свой Player Tag (например: #2ABC123), чтобы начать.",
                     reply_markup=markup)

# --- Сохраняем Player Tag ---
@bot.message_handler(func=lambda message: message.text.startswith("#"))
def save_tag(message):
    tag = message.text.strip().replace("#", "").upper()
    user_tags[message.chat.id] = tag
    bot.send_message(message.chat.id, f"✅ Твой Player Tag сохранён: #{tag}")

# --- Обработка кнопок ---
@bot.message_handler(func=lambda message: message.text in ["Текущие кубки", "Лучший боец",
                                                         "Топ игроков в стране", "Топ игроков в мире"])
def handle_buttons(message):
    chat_id = message.chat.id
    if chat_id not in user_tags:
        bot.send_message(chat_id, "❌ Сначала отправь свой Player Tag (например: #2ABC123)")
        return

    tag = user_tags[chat_id]

    # --- Текущие кубки и лучший боец ---
    if message.text in ["Текущие кубки", "Лучший боец"]:
        url = f"https://api.brawlstars.com/v1/players/%23{tag}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            bot.send_message(chat_id, "❌ Игрок не найден.")
            return
        data = response.json()

        if message.text == "Текущие кубки":
            bot.send_message(chat_id, f"🏆 Текущие кубки: {data['trophies']}")
        else:  # Лучший боец
            best_brawler = max(data["brawlers"], key=lambda b: b["trophies"])
            bot.send_message(chat_id,
                             f"👑 Лучший боец: {best_brawler['name']}\n"
                             f"🏆 Кубки на нём: {best_brawler['trophies']}")

    # --- Топ игроков ---
    elif message.text == "Топ игроков в стране":
        bot.send_message(chat_id, "Напиши код своей страны (например: UA, US, RU)")
        bot.register_next_step_handler(message, top_country)
    elif message.text == "Топ игроков в мире":
        top_global(chat_id)

# --- Функция: топ игроков по стране ---
def top_country(message):
    country_code = message.text.strip().upper()
    url = f"https://api.brawlstars.com/v1/rankings/players/country/{country_code}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        bot.send_message(message.chat.id, "❌ Страна не найдена или нет данных.")
        return
    data = response.json()
    text = f"🏅 Топ игроков в {country_code}:\n"
    for i, player in enumerate(data["items"][:10], 1):  # топ 10
        text += f"{i}. {player['name']} — {player['trophies']} кубков\n"
    bot.send_message(message.chat.id, text)

# --- Функция: топ игроков по миру ---
def top_global(chat_id):
    url = "https://api.brawlstars.com/v1/rankings/players"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        bot.send_message(chat_id, "❌ Ошибка получения глобального топа.")
        return
    data = response.json()
    text = "🌎 Топ игроков в мире:\n"
    for i, player in enumerate(data["items"][:10], 1):  # топ 10
        text += f"{i}. {player['name']} — {player['trophies']} кубков\n"
    bot.send_message(chat_id, text)

# --- Запуск бота ---
print("Бот запущен...")
bot.polling()
