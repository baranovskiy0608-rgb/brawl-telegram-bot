import os
import telebot
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BRAWL_API_KEY = os.getenv("BRAWL_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

headers = {
    "Authorization": f"Bearer {BRAWL_API_KEY}"
}


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет!\n\n"
        "Отправь мне свой Player Tag (пример: #2ABC123)"
    )


@bot.message_handler(func=lambda message: True)
def get_stats(message):
    tag = message.text.strip().replace("#", "").upper()

    url = f"https://api.brawlstars.com/v1/players/%23{tag}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        bot.send_message(message.chat.id, "❌ Игрок не найден.")
        return

    data = response.json()

    name = data["name"]
    trophies = data["trophies"]
    highest_trophies = data["highestTrophies"]

    best_brawler = max(data["brawlers"], key=lambda b: b["trophies"])

    text = (
        f"📊 Игрок: {name}\n\n"
        f"🏆 Кубки: {trophies}\n"
        f"🥇 Максимум: {highest_trophies}\n\n"
        f"👑 Лучший боец: {best_brawler['name']}\n"
        f"🏆 Кубки на нём: {best_brawler['trophies']}"
    )

    bot.send_message(message.chat.id, text)


print("Бот запущен...")
bot.polling()
