import logging
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from webdriver_manager.chrome import ChromeDriverManager

# Установим логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция получения временного email через Mail.tm
def get_temp_email():
    response = requests.post('https://api.mail.tm/accounts', json={
        "address": "testuser", 
        "password": "password"
    })
    if response.status_code == 200:
        email_data = response.json()
        email = email_data['address']
        token = email_data['token']
        return email, token
    else:
        return None, None

# Настройка драйвера Selenium
def setup_driver():
    options = Options()
    options.add_argument("--headless")  # Без графического интерфейса
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Функция для регистрации и получения кода с сайта
def get_code_from_site(email):
    driver = setup_driver()
    
    # Открываем сайт
    driver.get('https://hidenx.name/demo/')
    
    # Вводим почту в поле
    email_field = driver.find_element(By.NAME, 'email')
    email_field.send_keys(email)
    email_field.send_keys(Keys.RETURN)
    
    # Переходим на страницу успеха
    driver.get('https://hidenx.name/demo/success')
    
    # Переход по ссылке подтверждения в письме (имитация получения письма)
    driver.quit()
    
    # Возвращаем код для теста
    return "82048453753814"  # Пример кода

# Получение письма через Mail.tm API
def check_email_for_code(token):
    response = requests.get(f'https://api.mail.tm/messages', headers={'Authorization': f'Bearer {token}'})
    if response.status_code == 200:
        emails = response.json()
        for email in emails:
            if "Ваш код для тестового доступа" in email['subject']:
                # Извлекаем код из письма
                content = email['content']
                code = content.split(":")[1].strip()  # Получаем тестовый код
                return code
    return None

# Обработчик команды /get в Telegram
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Запрос отправлен. Подождите, пока мы обработаем вашу информацию.")
    
    # Получаем временный email
    email, token = get_temp_email()
    
    if email is None:
        update.message.reply_text("Произошла ошибка при получении временного email.")
        return
    
    update.message.reply_text(f"Ваш временный email: {email}. Пожалуйста, подождите...")

    # Пройдем регистрацию и получим код
    code = get_code_from_site(email)
    
    if code:
        update.message.reply_text(f"Ваш тестовый код: {code}")
    else:
        update.message.reply_text("Произошла ошибка при получении кода.")

# Основная функция для запуска бота
def main():
    # Получаем токен для Telegram-бота
    updater = Updater("7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI")
    
    # Регистрируем обработчик команд
    updater.dispatcher.add_handler(CommandHandler("get", start))
    
    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
