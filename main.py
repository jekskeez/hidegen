from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Ваш Telegram токен
TOKEN = '7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI'

# Словарь для хранения почтовых ящиков пользователей
user_emails = {}

# Функция для обработки команды /get
def get_code(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    email = create_temp_email()  # Функция создания временной почты
    user_emails[user_id] = email
    
    # Отправляем пользователю временную почту
    update.message.reply_text(f'Ваша временная почта: {email}')

    # Теперь запускаем процесс автоматического получения тестового кода
    get_vpn_code(email)

def create_temp_email():
    """Функция для создания временной почты с использованием mail.tm"""
    import pymailtm
    # Создаем почту с помощью pymailtm
    client = pymailtm.Client()
    return client.create_email()

def get_vpn_code(email):
    """Функция для получения тестового кода через сайт HideMyName"""
    import requests
    from bs4 import BeautifulSoup
    import time

    # Переходим на страницу регистрации
    demo_url = 'https://hidenx.name/demo/'
    session = requests.Session()

    # Заполняем почтовый адрес на форме
    payload = {'email': email}
    response = session.post(demo_url, data=payload)

    # Проверяем, что перенаправление прошло
    if response.url == 'https://hidenx.name/demo/success':
        print("Redirected to success page")

        # Ожидаем получения письма с подтверждением
        wait_for_email_confirmation(email)
        
        # После подтверждения почты ждем код
        get_code_from_email(email)

def wait_for_email_confirmation(email):
    """Функция для ожидания письма с подтверждением"""
    import time
    import pymailtm
    client = pymailtm.Client()

    # Ждем подтверждения письма
    while True:
        emails = client.get_inbox(email)
        for message in emails:
            if 'Подтвердите e-mail' in message['subject']:
                # Найдено письмо, нажимаем на ссылку подтверждения
                confirmation_link = message['text'].split("href=\"")[1].split("\"")[0]
                requests.get(confirmation_link)
                print("Email confirmed")
                return
        time.sleep(5)  # Проверяем почту каждую секунду

def get_code_from_email(email):
    """Функция для получения тестового кода из письма"""
    import pymailtm
    client = pymailtm.Client()

    while True:
        emails = client.get_inbox(email)
        for message in emails:
            if 'Ваш код для тестового доступа' in message['subject']:
                code = message['text'].split("Ваш тестовый код: ")[1].strip()
                print(f"Получен код: {code}")
                send_code_to_user(code)
                return
        time.sleep(5)

def send_code_to_user(code):
    """Отправка кода пользователю в Telegram"""
    import telegram
    bot = telegram.Bot(token=TOKEN)

    for user_id, email in user_emails.items():
        bot.send_message(user_id, f"Ваш тестовый код: {code}")

# Основная функция
def main():
    updater = Updater(TOKEN)

    # Добавляем обработчик команды /get
    updater.dispatcher.add_handler(CommandHandler("get", get_code))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
