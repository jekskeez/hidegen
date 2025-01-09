import time
import requests
from telegram import Update
from telegram.ext import CommandHandler, ApplicationBuilder
from bs4 import BeautifulSoup
from pymailtm import MailTm

# Инициализация клиента для работы с Mail.tm
mail_client = MailTm()

# Функция для создания нового почтового ящика
def create_email():
    # Создаем новый почтовый ящик
    account = mail_client._open_account()  # или используйте другой метод, если доступен для создания
    if account:
        email = account['address']  # Получаем созданный email
        print(f"Почта успешно создана: {email}")
        return email
    else:
        print("Не удалось создать почту.")
        return None

# Функция для получения почтового ящика
def get_inbox(email):
    # Получаем все письма в почтовом ящике
    inbox = mail_client.get_inbox(email)
    return inbox

# Ссылка на демо-страницу HideMyName
demo_url = 'https://hidenx.name/demo/'

# Функция для регистрации на сайте с использованием почты
def register_on_site(email):
    # Создаем сессию и заходим на страницу
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

# Функция для подтверждения почты
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

# Функция для получения тестового кода
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
    email = create_email()
    if email is None:
        await update.message.reply_text("Произошла ошибка при генерации почты.")
        return

    # Регистрация на сайте с этой почтой
    if not register_on_site(email):
        await update.message.reply_text("Ошибка при регистрации на сайте.")
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

# Используем текущий цикл событий
def main():
    # Вставьте ваш токен бота
    TELEGRAM_TOKEN = '7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI'
    
    # Инициализация бота
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("get", get_test_code_telegram))
    
    # Запуск бота
    application.run_polling()

# Вместо asyncio.run, используем get_event_loop для запуска в текущем цикле
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
