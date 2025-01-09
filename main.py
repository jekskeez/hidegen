import logging
import requests
import uuid
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

# Функция для получения токена
def get_token(address, password):
    url = 'https://api.mail.tm/token'
    payload = {
        "address": address,
        "password": password
    }

    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data['token']
    else:
        logger.error(f"Ошибка получения токена. Код ошибки: {response.status_code}")
        return None

# Функция получения списка доменов
def get_domains(token):
    url = 'https://api.mail.tm/domains'
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        domains_data = response.json()
        if domains_data["hydra:member"]:
            domain = domains_data["hydra:member"][0]["domain"]  # Берем первый доступный домен
            return domain
        else:
            logger.error("Нет доступных доменов.")
            return None
    else:
        logger.error(f"Ошибка получения доменов. Код ошибки: {response.status_code}")
        return None

# Функция создания временной почты
def create_temp_email(token, domain):
    random_name = str(uuid.uuid4().hex)  # Генерация уникального имени
    email_address = f"{random_name}@{domain}"
    
    url = 'https://api.mail.tm/accounts'
    payload = {
        "address": email_address,
        "password": "password"
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        email_data = response.json()
        email = email_data['address']
        return email
    else:
        logger.error(f"Ошибка создания почты. Код ошибки: {response.status_code}")
        return None

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
    address = "your_email@example.com"  # Укажите свою почту для получения токена
    password = "your_password"  # Укажите пароль для этой почты
    token = get_token(address, password)
    
    if token:
        domain = get_domains(token)  # Получаем домен
        if domain:
            email = create_temp_email(token, domain)  # Создаем временный email
            if email:
                await update.message.reply_text(f"Ваш временный email: {email}. Пожалуйста, подождите...")
                
                # Пройдем регистрацию и получим код
                code = get_code_from_site(email)
                
                if code:
                    await update.message.reply_text(f"Ваш тестовый код: {code}")
                else:
                    await update.message.reply_text("Произошла ошибка при получении кода.")
            else:
                await update.message.reply_text("Не удалось создать временный email.")
        else:
            await update.message.reply_text("Не удалось получить домен.")
    else:
        await update.message.reply_text("Не удалось получить токен.")

# Основная функция для запуска бота
async def main():
    # Получаем токен для Telegram-бота
    application = Application.builder().token("7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI").build()
    
    # Регистрируем обработчик команд
    application.add_handler(CommandHandler("get", start))
    
    # Запускаем бота
    await application.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()  # Разрешает использование event loop в Jupyter или других подобных средах
    import asyncio
    asyncio.run(main())  # Запускаем асинхронную функцию main
