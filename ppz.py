import requests
import time
import re
from telegram import Bot
from telegram.ext import Updater, CommandHandler

# Константы
API_EMAILNATOR = "https://api.emailnator.com"
TELEGRAM_TOKEN = "7505320830:AAFa_2WvRVEo_I1YkiO-RQDS2FwGtLJY1po"

# Функция для генерации почты через API Emailnator
def generate_email():
    url = f"{API_EMAILNATOR}/generate-email"
    response = requests.post(url)
    email = response.json().get("email")
    return email

# Функция для регистрации на сайте
def register_on_site(email):
    url = "https://hixxxx.name/demo"
    data = {
        "email": email
    }
    response = requests.post(url, data=data)
    
    if "Тестовый доступ уже был запрошен ранее" in response.text:
        return False  # Почта уже использована, нужно пробовать снова
    return True  # Почта подходит

# Функция для получения сообщений на почту
def get_email_messages(email):
    url = f"{API_EMAILNATOR}/inbox"
    response = requests.post(url, data={"email": email})
    return response.json().get("messages", [])

# Функция для извлечения ссылки подтверждения из письма
def extract_confirmation_link(email_content):
    match = re.search(r"https://[^\s]+", email_content)
    return match.group(0) if match else None

# Функция для извлечения кода из письма
def extract_code(email_content):
    match = re.search(r"Ваш тестовый код: (\d+)", email_content)
    return match.group(1) if match else None

# Функция для отправки кода пользователю в Telegram
def send_code_to_user(chat_id, code):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=chat_id, text=f"Ваш тестовый код: {code}")

# Основная логика бота
def process_registration(update, context):
    # Шаг 1: Генерация почты
    email = generate_email()
    update.message.reply_text(f"Генерируем почту: {email}")

    # Шаг 2: Регистрация на сайте
    while not register_on_site(email):
        email = generate_email()  # Пробуем снова с новой почтой
        update.message.reply_text(f"Почта уже использована, пробуем другую: {email}")
    
    update.message.reply_text(f"Регистрация успешна для {email}, ждем письмо с подтверждением!")

    # Шаг 3: Ожидание письма с подтверждением
    confirmation_link = None
    while not confirmation_link:
        time.sleep(5)  # Ждем 5 секунд перед следующей попыткой
        messages = get_email_messages(email)
        for message in messages:
            if message.get("subject") == "Подтвердите e-mail":
                confirmation_link = extract_confirmation_link(message.get("body", ""))
                if confirmation_link:
                    update.message.reply_text(f"Ссылка для подтверждения: {confirmation_link}")
                    break
    
    # Шаг 4: Переход по ссылке (имитация клика)
    update.message.reply_text(f"Переходим по ссылке: {confirmation_link}")
    requests.get(confirmation_link)

    # Шаг 5: Ожидание письма с кодом
    code = None
    while not code:
        time.sleep(5)  # Ждем 5 секунд перед следующей попыткой
        messages = get_email_messages(email)
        for message in messages:
            if message.get("subject") == "Ваш код для тестового доступа к сервису":
                code = extract_code(message.get("body", ""))
                if code:
                    send_code_to_user(update.message.chat_id, code)
                    update.message.reply_text(f"Код отправлен в Telegram: {code}")
                    break

# Основной запуск бота
def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("get", process_registration))  # Запуск через команду /get
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
