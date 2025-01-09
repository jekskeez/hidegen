import time
import requests
from pymailtm import MailTm
from telegram import Update
from telegram.ext import CommandHandler, ApplicationBuilder
from bs4 import BeautifulSoup

# Инициализация клиента для работы с Mail.tm
mail_client = MailTm()

# Функция для получения случайного адреса
def get_random_email():
    return mail_client.random_username()

# Функция для получения почты
def get_inbox(email):
    return mail_client.get_inbox(email)

# Ссылка на демо-страницу HideMyName
demo_url = 'https://hidenx.name/demo/'

def get_demo_code():
    # Генерация случайного email
    email = get_random_email()

    # Делаем запрос на форму
    session = requests.Session()
    response = session.get(demo_url)
    
    if response.status_code != 200:
        print("Не удалось загрузить страницу")
        return None
    
    # Находим скрытые поля формы
    soup = BeautifulSoup(response.text, 'html.parser')
    hidden_inputs = soup.find_all('input', type='hidden')
    form_data = {input['name']: input['value'] for input in hidden_inputs}
    form_data['email'] = email

    # Отправляем email на сервер
    response = session.post(demo_url, data=form_data)
    
    if 'success' in response.url:
        print(f"Почта {email} успешно отправлена.")
        return email
    else:
        print("Ошибка при отправке почты.")
        return None

def confirm_email(email):
    # Проверка почты на наличие письма с подтверждением
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

def get_test_code(email):
    # После подтверждения почты ждем письмо с тестовым кодом
    inbox = get_inbox(email)
    
    for email_data in inbox:
        if "Ваш код для тестового доступа к сервису" in email_data['subject']:
            # Извлекаем тестовый код из тела письма
            code = email_data['body']['text']['plain']
            # Находим код в тексте
            test_code = code.split(":")[1].strip()
            print(f"Тестовый код: {test_code}")
            return test_code
    return None

# Телеграм боты и обработка команд

async def start(update: Update, context):
    await update.message.reply_text("Привет! Отправь команду /get, чтобы получить тестовый код.")

async def get_test_code_telegram(update: Update, context):
    # Генерация почты и получение кода
    email = get_demo_code()
    if email is None:
        await update.message.reply_text("Произошла ошибка при генерации почты.")
        return

    # Подтверждение почты
    if not confirm_email(email):
        await update.message.reply_text("Не удалось подтвердить почту.")
        return
    
    # Получаем тестовый код
    test_code = get_test_code(email)
    if test_code:
        await update.message.reply_text(f"Ваш тестовый код: {test_code}")
    else:
        await update.message.reply_text("Не удалось получить тестовый код.")

async def main():
    # Вставьте ваш токен бота
    TELEGRAM_TOKEN = '7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI'
    
    # Инициализация бота
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("get", get_test_code_telegram))
    
    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
