import http.client
import requests
import re
import time
from telegram import Bot
from telegram.ext import Application, CommandHandler

# Константы
API_EMAILNATOR = "https://gmailnator.p.rapidapi.com"
RAPIDAPI_KEY = "ad1b3054edmsh789f00e777ead14p1af3bcjsn948b23294e77"
TELEGRAM_TOKEN = "7505320830:AAFa_2WvRVEo_I1YkiO-RQDS2FwGtLJY1po"

# Функция для генерации почты через API Emailnator (через RapidAPI)
def generate_email():
    conn = http.client.HTTPSConnection("gmailnator.p.rapidapi.com")

    payload = "{\"options\":[3]}"

    headers = {
        'x-rapidapi-key': RAPIDAPI_KEY,
        'x-rapidapi-host': "gmailnator.p.rapidapi.com",
        'Content-Type': "application/json"
    }

    conn.request("POST", "/generate-email", payload, headers)

    res = conn.getresponse()
    data = res.read()

    print(data.decode("utf-8"))

    # Извлекаем почту из ответа API
    response_data = data.decode("utf-8")
    email = re.search(r'"email":\s*"([^"]+)"', response_data)
    return email.group(1) if email else None

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
    conn = http.client.HTTPSConnection("gmailnator.p.rapidapi.com")

    payload = "{\"email\":\"" + email + "\",\"limit\":10}"

    headers = {
        'x-rapidapi-key': RAPIDAPI_KEY,
        'x-rapidapi-host': "gmailnator.p.rapidapi.com",
        'Content-Type': "application/json"
    }

    conn.request("POST", "/inbox", payload, headers)

    res = conn.getresponse()
    data = res.read()

    return data.decode("utf-8")

# Функция для извлечения ссылки подтверждения из HTML
def extract_confirmation_link_from_html(html_content):
    match = re.search(r'<a [^>]*href=\\?"(https?://[^\s]+)"[^>]*>Подтвердить</a>', html_content)
    if match:
        return match.group(1)
    return None

# Функция для отправки кода пользователю в Telegram
def send_code_to_user(chat_id, code):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=chat_id, text=f"Ваш тестовый код: {code}")

# Основная логика бота
async def process_registration(update, context):
    # Шаг 1: Генерация почты
    email = generate_email()
    if email is None:
        await update.message.reply_text("Ошибка при генерации почты.")
        return

    await update.message.reply_text(f"Генерируем почту: {email}")

    # Шаг 2: Регистрация на сайте
    while not register_on_site(email):
        email = generate_email()  # Пробуем снова с новой почтой
        await update.message.reply_text(f"Почта уже использована, пробуем другую: {email}")
    
    await update.message.reply_text(f"Регистрация успешна для {email}, ждем письмо с подтверждением!")

    # Шаг 3: Ожидание письма с подтверждением
    confirmation_link = None
    while not confirmation_link:
        time.sleep(5)  # Ждем 5 секунд перед следующей попыткой
        messages = get_email_messages(email)
        # Проверяем каждое сообщение
        for message in messages.split('},'):
            if '"subject": "Подтвердите e-mail"' in message:
                # Извлекаем ссылку из HTML
                confirmation_link = extract_confirmation_link_from_html(message)
                if confirmation_link:
                    await update.message.reply_text(f"Ссылка для подтверждения: {confirmation_link}")
                    break
    
    # Шаг 4: Переход по ссылке (имитация клика)
    await update.message.reply_text(f"Переходим по ссылке: {confirmation_link}")
    response = requests.get(confirmation_link)
    if response.status_code == 200:
        await update.message.reply_text("Подтверждение прошло успешно.")
    else:
        await update.message.reply_text("Ошибка при переходе по ссылке.")

    # Шаг 5: Ожидание письма с кодом
    code = None
    while not code:
        time.sleep(5)  # Ждем 5 секунд перед следующей попыткой
        messages = get_email_messages(email)
        for message in messages.split('},'):
            if '"subject": "Ваш код для тестового доступа к сервису"' in message:
                # Извлекаем код из письма
                match = re.search(r"Ваш тестовый код: (\d+)", message)
                if match:
                    code = match.group(1)
                    send_code_to_user(update.message.chat_id, code)
                    await update.message.reply_text(f"Код отправлен в Telegram: {code}")
                    break

# Основной запуск бота
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("get", process_registration))  # Запуск через команду /get
    application.run_polling()

if __name__ == "__main__":
    main()
