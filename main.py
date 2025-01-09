import os
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, ApplicationBuilder
from bs4 import BeautifulSoup
from pymailtm import MailTm
import requests
import random
import string

# Убедитесь, что директория для базы данных MailTm существует
os.makedirs(os.path.expanduser("~/.pymailtm"), exist_ok=True)

# Инициализация клиента для работы с Mail.tm
mail_client = MailTm()

def generate_username(length=8):
    """Генерация случайного имени пользователя."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_available_domains():
    """Получение списка доступных доменов с помощью API Mail.tm."""
    try:
        response = requests.get("https://api.mail.tm/domains")
        if response.status_code == 200:
            data = response.json()
            return [domain['domain'] for domain in data['hydra:member']]
        else:
            print(f"Не удалось получить список доменов. Код ответа: {response.status_code}")
            return []
    except Exception as e:
        print(f"Ошибка при получении доменов: {e}")
        return []

def create_email():
    try:
        # Получаем список доступных доменов через API
        domains = get_available_domains()
        if not domains:
            print("Список доменов пуст.")
            return None
        
        # Выбираем первый доступный домен
        domain = domains[0]
        username = generate_username()
        address = f"{username}@{domain}"

        # Создаем аккаунт
        account = mail_client.create_account(address, password=generate_username(12))
        if account:
            email = account['address']
            print(f"Почта успешно создана: {email}")
            return email
        else:
            print("Не удалось создать почту.")
            return None
    except Exception as e:
        print(f"Ошибка при создании почты: {e}")
        return None

def get_inbox(email):
    try:
        inbox = mail_client.get_inbox(email)
        return inbox
    except Exception as e:
        print(f"Ошибка при получении писем: {e}")
        return []

demo_url = 'https://hidenx.name/demo/'

def register_on_site(email):
    try:
        session = requests.Session()
        response = session.get(demo_url)

        if response.status_code != 200:
            print("Не удалось загрузить страницу")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        hidden_inputs = soup.find_all('input', type='hidden')
        form_data = {input['name']: input['value'] for input in hidden_inputs}
        form_data['email'] = email

        response = session.post(demo_url, data=form_data)

        if 'success' in response.url:
            print(f"Почта {email} успешно отправлена.")
            return email
        else:
            print("Ошибка при отправке почты.")
            return None
    except Exception as e:
        print(f"Ошибка при регистрации: {e}")
        return None

def confirm_email(email):
    try:
        inbox = get_inbox(email)

        for email_data in inbox:
            if "Подтвердите e-mail" in email_data['subject']:
                confirm_url = email_data['body']['text']['plain'].strip()
                response = requests.get(confirm_url)
                if response.status_code == 200:
                    print("Почта подтверждена.")
                    return True
        print("Не найдено письмо для подтверждения.")
        return False
    except Exception as e:
        print(f"Ошибка при подтверждении почты: {e}")
        return False

def get_test_code(email):
    try:
        inbox = get_inbox(email)

        for email_data in inbox:
            if "Ваш код для тестового доступа к сервису" in email_data['subject']:
                code = email_data['body']['text']['plain']
                test_code = code.split(":")[1].strip()
                print(f"Тестовый код: {test_code}")
                return test_code
        return None
    except Exception as e:
        print(f"Ошибка при получении тестового кода: {e}")
        return None

async def start(update: Update, context):
    await update.message.reply_text("Привет! Отправь команду /get, чтобы получить тестовый код.")

async def get_test_code_telegram(update: Update, context):
    email = create_email()
    if email is None:
        await update.message.reply_text("Произошла ошибка при генерации почты.")
        return

    if not register_on_site(email):
        await update.message.reply_text("Ошибка при регистрации на сайте.")
        return

    if not confirm_email(email):
        await update.message.reply_text("Не удалось подтвердить почту.")
        return

    test_code = get_test_code(email)
    if test_code:
        await update.message.reply_text(f"Ваш тестовый код: {test_code}")
    else:
        await update.message.reply_text("Не удалось получить тестовый код.")

def main():
    TELEGRAM_TOKEN = '7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI'

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("get", get_test_code_telegram))

    application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
