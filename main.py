import time
import requests
from pymailtm import MailTm
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Создаем объект для работы с API Mail.tm
mailtm = MailTm()

# Функция для получения почтового ящика
def get_temp_email():
    # Получаем временную почту
    mailbox = mailtm.get_mailbox()
    email_address = mailbox['address']
    return email_address

# Функция для проверки новых писем на Mail.tm
def check_email(email_address):
    while True:
        messages = mailtm.get_messages(email_address)
        if messages:
            for message in messages:
                if 'Подтвердите e-mail' in message['subject']:
                    # Найдем ссылку для подтверждения
                    confirm_link = message['text'].split('href="')[1].split('"')[0]
                    print(f"Confirm link: {confirm_link}")
                    return confirm_link
        time.sleep(5)

# Подтверждаем почту
def confirm_email(confirm_link):
    response = requests.get(confirm_link)
    if response.status_code == 200:
        print("Email confirmed successfully.")
    else:
        print("Failed to confirm email.")

# Функция для получения тестового кода из письма
def get_access_code(email_address):
    while True:
        messages = mailtm.get_messages(email_address)
        for message in messages:
            if 'Ваш код для тестового доступа' in message['subject']:
                code = message['text'].split('Ваш тестовый код: ')[1].strip()
                print(f"Test code: {code}")
                return code
        time.sleep(5)

# Отправка тестового кода в Telegram
async def send_code_to_user(user_id, code):
    bot = Bot(token="7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI")
    message = f"Ваш тестовый код: {code}"
    await bot.send_message(chat_id=user_id, text=message)

# Основная функция для команды /get
async def get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    
    # Получаем новый почтовый ящик
    email_address = get_temp_email()
    print(f"Generated email: {email_address}")
    
    # Шлем запрос на сайт для получения письма
    demo_url = "https://hidenx.name/demo/"
    response = requests.get(demo_url, params={"email": email_address})
    
    # Проверка письма с подтверждением
    print("Checking email for confirmation link...")
    confirm_link = check_email(email_address)
    
    # Подтверждаем почту
    print("Confirming email...")
    confirm_email(confirm_link)
    
    # Получаем тестовый код
    print("Getting test code...")
    test_code = get_access_code(email_address)
    
    # Отправляем код пользователю
    await send_code_to_user(user_id, test_code)
    await update.message.reply_text("Ваш тестовый код был отправлен!")

# Настройка и запуск бота
def main():
    application = Application.builder().token("7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI").build()

    # Добавляем обработчик команды /get
    application.add_handler(CommandHandler("get", get_code))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
