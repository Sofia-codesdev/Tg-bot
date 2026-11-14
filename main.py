import telebot
from telebot import types
import requests
import datetime
import csv
import os
import config

bot = telebot.TeleBot(config.TOKEN)

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_logs.csv")
 

# лонирование
def log_action(user_id, username, motion, api_name="NONE", api_answer="NONE"):
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Unic ID', '@TG nick', 'Motion', 'API', 'Date', 'Time', 'API_answer'])

        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        clean_answer = str(api_answer).replace('\n', ' ').replace('\r', '')

        writer.writerow([
            user_id,
            f"@{username}",
            motion,
            api_name,
            date_str,
            time_str,
            clean_answer
        ])


# погода в Минске
def get_weather():
    lat, lon = 53.9006, 27.5590
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        temp = data['current_weather']['temperature']
        wind = data['current_weather']['windspeed']
        return f"🌤 Погода в Минске:\nТемпература: {temp}°C\nСкорость ветра: {wind} км/ч"
    except Exception as e:
        return f"Ошибка получения погоды: {e}"


# курс валют
def get_currency():
    url = "https://api.nbrb.by/exrates/rates?periodicity=0"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        result = "💵 Курсы валют НБРБ:\n"
        for rate in data:
            if rate['Cur_Abbreviation'] in ['USD', 'EUR', 'RUB']:
                result += f"{rate['Cur_Scale']} {rate['Cur_Abbreviation']}: {rate['Cur_OfficialRate']} BYN\n"
        return result
    except Exception as e:
        return f"Ошибка получения курса: {e}"


def get_fact():
    url = "https://ru.wikipedia.org/api/rest_v1/page/random/summary"
    headers = {
        "User-Agent": "LabBot/1.0 (https://github.com/your_username/your_repo; your_email@example.com)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', 'Без названия')
            extract = data.get('extract', 'Нет описания')
            if len(extract) > 500:
                extract = extract[:500] + "..."
            return f"📚 Случайная статья из Википедии:\n\n*{title}*\n\n{extract}"
        else:
            return f"Не удалось получить факт (код: {response.status_code})"
    except Exception as e:
        return f"Ошибка получения факта: {e}"

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2) # было 3, стало 2
    btn_weather = types.KeyboardButton("Погода")
    btn_currency = types.KeyboardButton("Курс валют")
    btn_fact = types.KeyboardButton("Факт")
    markup.add(btn_weather, btn_currency)
    markup.add(btn_fact)
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    username = message.from_user.username or "no_username"
    log_action(message.from_user.id, username, "Start Command")

    bot.send_message(
        message.chat.id,
        "Привет! Я бот для лабораторной работы.\n"
        "Выбери действие на клавиатуре 👇",
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(content_types=['text'])
def text_handler(message):
    user_text = message.text
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    # Погода
    if user_text == "Погода":
        answer = get_weather()
        bot.send_message(message.chat.id, answer)
        log_action(user_id, username, "Button Click", "Open-Meteo (Weather)", answer)

    # Курс валют
    elif user_text == "Курс валют":
        answer = get_currency()
        bot.send_message(message.chat.id, answer)
        log_action(user_id, username, "Button Click", "NBRB (Currency)", answer)

    # Рандомный факт
    elif user_text == "Факт":
        answer = get_fact()
        bot.send_message(message.chat.id, answer, parse_mode='Markdown')
        log_action(user_id, username, "Button Click", "Wikipedia (Fact)", answer)

    else:
        answer = f'Вы написали "{user_text}", я не знаю такой команды'
        bot.send_message(message.chat.id, answer)
        log_action(user_id, username, "Keyboard typing", "NONE", "NONE")


if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()