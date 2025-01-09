import logging
import time
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from pymailtm import MailTM, MailTMClient

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен бота
TELEGRAM_TOKEN = "7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI"  # Замените на свой токен

# Инициализация Mail.tm клиента
mail_client = MailTMClient()
mail_client.login()

# Функция для создания временной почты через Mail.tm
def create_temp_email():
    email = mail_client.create_email()
    return email

# Функция для получения почты
def get_email_inbox(email):
    # Проверка входящих писем
    return mail_client.get_inbox(email)

# Функция для извлечения кода из письма
def extract_code_from_email(inbox):
    for email in inbox:
        if "Ваш код для тестового доступа" in email['subject']:
            # Извлекаем тестовый код
            match = re.search(r"Ваш тестовый код: (\d+)", email['body'])
            if match:
                return match.group(1)
    return None

# Функция для отправки тестового запроса через сайт
def request_demo_access(email):
    # Шаг 1: Переходим по ссылке и вводим email
    url = "https://hidenx.name/demo/"
    session = requests.Session()
    response = session.get(url)
    
    # Предположим, что здесь происходит процесс ввода email на сайте
    # Имитация отправки email на сайт
    data = {'email': email}
    response = session.post(url, data=data)
    
    # Шаг 2: Проверка перенаправления
    if response.url == "https://hidenx.name/demo/success":
        return True
    return False

# Функция для обработки команды /get
def get_test_code(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    update.message.reply_text("Создаю временную почту...")
    
    # Создаем временный email
    temp_email = create_temp_email()
    update.message.reply_text(f"Ваша временная почта: {temp_email}")
    
    update.message.reply_text("Перехожу на сайт и ввожу почту...")
    
    # Шаг 1: Пытаемся запросить доступ
    success = request_demo_access(temp_email)
    
    if not success:
        update.message.reply_text("Не удалось пройти авторизацию на сайте.")
        return
    
    update.message.reply_text("Процесс регистрации завершен. Ожидаю письмо для подтверждения...")

    # Шаг 2: Ожидаем письмо для подтверждения
    timeout = 60  # 1 минута на подтверждение
    start_time = time.time()
    while time.time() - start_time < timeout:
        inbox = get_email_inbox(temp_email)
        for email in inbox:
            if "Подтвердите e-mail" in email['subject']:
                # Извлекаем ссылку для подтверждения
                confirm_link = re.search(r'href="(https://hidenx.name/demo/confirm/\S+)"', email['body'])
                if confirm_link:
                    confirmation_url = confirm_link.group(1)
                    # Переходим по ссылке для подтверждения
                    requests.get(confirmation_url)
                    update.message.reply_text("Почта подтверждена, ожидаю код доступа...")
                    break
        else:
            time.sleep(5)  # Проверяем почту каждую секунду
            continue
        break
    
    # Шаг 3: Ожидаем письмо с кодом
    timeout = 120  # 2 минуты на получение кода
    start_time = time.time()
    while time.time() - start_time < timeout:
        inbox = get_email_inbox(temp_email)
        code = extract_code_from_email(inbox)
        if code:
            update.message.reply_text(f"Ваш тестовый код: {code}")
            break
        else:
            time.sleep(5)  # Проверяем почту каждую секунду

    else:
        update.message.reply_text("Не удалось получить код доступа.")

# Функция для обработки ошибок
def error(update: Update, context: CallbackContext):
    logger.warning(f"Update {update} caused error {context.error}")

# Основная функция для запуска бота
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Обработчик команды /get
    dispatcher.add_handler(CommandHandler("get", get_test_code))
    
    # Обработчик ошибок
    dispatcher.add_error_handler(error)
    
    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
