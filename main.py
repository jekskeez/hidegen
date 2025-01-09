import logging
import uuid
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from webdriver_manager.chrome import ChromeDriverManager

# Установим логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция получения временного email через Mail.tm
def get_temp_email():
    url = 'https://api.mail.tm/accounts'
    
    # Генерируем уникальное имя для почты
    random_name = str(uuid.uuid4().hex)  # Генерация уникального имени с помощью UUID
    email_address = f"{random_name}@mail.tm"  # Пример генерации уникального email

    payload = {
        "address": email_address,
        "password": "password"
    }

    try:
        response = requests.post(url, json=payload)
        print("Ответ от API:", response.text)  # Выводим ответ от API для отладки

        if response.status_code == 200:
            email_data = response.json()
            email = email_data['address']
            token = email_data['token']
            return email, token
        else:
            print(f"Ошибка при создании почты. Код ошибки: {response.status_code}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"Произошла ошибка при запросе к API Mail.tm: {e}")
        return None, None

# Тестируем функцию получения почты
email, token = get_temp_email()
if email:
    print(f"Временный email: {email}, Токен: {token}")
else:
    print("Не удалось получить временный email.")
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
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Запрос отправлен. Подождите, пока мы обработаем вашу информацию.")
    
    # Получаем временный email
    email, token = get_temp_email()
    
    if email is None:
        await update.message.reply_text("Произошла ошибка при получении временного email.")
        return
    
    await update.message.reply_text(f"Ваш временный email: {email}. Пожалуйста, подождите...")

    # Пройдем регистрацию и получим код
    code = get_code_from_site(email)
    
    if code:
        await update.message.reply_text(f"Ваш тестовый код: {code}")
    else:
        await update.message.reply_text("Произошла ошибка при получении кода.")

# Основная функция для запуска бота
async def main():
    # Получаем токен для Telegram-бота
    application = Application.builder().token("7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI").build()
    
    # Регистрируем обработчик команд
    application.add_handler(CommandHandler("get", start))
    
    # Запускаем бота
    await application.run_polling()

# Вместо asyncio.run(main()) используем await main() прямо в активном цикле
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()  # Это необходимо для работы с уже активным циклом в Colab
    import asyncio
    asyncio.run(main())  # Запускаем асинхронную функцию
