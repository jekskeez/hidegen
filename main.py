import time
import requests
import random
import string
import logging
import telebot
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Ваш токен Telegram-бота
TELEGRAM_TOKEN = "7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Функция для генерации случайного почтового адреса
def generate_random_email():
    """Генерация случайного почтового адреса"""
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{random_string}@mail.tm"

# Функция для получения новой временной почты с API Mail.tm
def get_mail():
    try:
        email_address = generate_random_email()  # Генерация уникального адреса
        email_data = {'address': email_address, 'password': 'password123'}
        
        # Отправка запроса на создание почты
        response = requests.post('https://api.mail.tm/accounts', json=email_data)
        
        # Проверка статуса ответа
        if response.status_code == 201:
            mail = response.json()
            email = mail['address']
            token = mail['token']
            logger.info(f"Получена почта: {email}")
            return email, token
        else:
            handle_api_error(response)
            return None, None
    except Exception as e:
        logger.error(f"Ошибка при получении почты: {str(e)}")
        return None, None

# Обработка ошибок от API
def handle_api_error(response):
    """Обработка ошибок при запросах к API"""
    if response.status_code == 422:
        logger.error(f"Ошибка при создании почты: {response.status_code} - Не удается обработать запрос. Проверьте формат данных.")
        logger.error(f"Текст ошибки: {response.text}")
    elif response.status_code == 400:
        logger.error(f"Ошибка в запросе: {response.status_code} - Некорректные данные.")
        logger.error(f"Текст ошибки: {response.text}")
    elif response.status_code == 500:
        logger.error(f"Ошибка сервера: {response.status_code} - Проблемы на сервере Mail.tm.")
        logger.error(f"Текст ошибки: {response.text}")
    else:
        logger.error(f"Неизвестная ошибка: {response.status_code} - {response.text}")

# Инициализация WebDriver
def init_driver():
    try:
        options = Options()
        options.add_argument("--headless")  # Для безголового режима
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        logger.info("WebDriver инициализирован")
        return driver
    except Exception as e:
        logger.error(f"Ошибка при инициализации WebDriver: {str(e)}")
        return None

# Функция для автоматического ввода почты и получения перенаправления
def submit_email_and_get_code(driver, email):
    try:
        driver.get("https://hidenx.name/demo/")

        # Находим поле для ввода почты
        email_input = driver.find_element(By.NAME, "email")
        email_input.send_keys(email)
        email_input.send_keys(Keys.RETURN)

        # Ждем перенаправления на success
        time.sleep(3)  # Можно заменить на явные ожидания
        if "success" in driver.current_url:
            logger.info(f"Почта {email} успешно отправлена на сайт, перенаправление прошло.")
            return True
        else:
            logger.error(f"Не удалось перенаправить на страницу успеха после ввода почты {email}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при отправке почты на сайт: {str(e)}")
        return False

# Функция для проверки почты на наличие письма с подтверждением
def check_mail_for_confirmation(token):
    try:
        url = f"https://api.mail.tm/messages"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Ошибка при получении писем, статус: {response.status_code}")
            return None
        
        messages = response.json()
        for msg in messages:
            if "Подтвердите e-mail" in msg['subject']:
                confirmation_url = msg['text']  # Это пример, нужно уточнить, как передается ссылка в тексте письма
                logger.info("Найдено письмо с подтверждением.")
                return confirmation_url
        logger.info("Письмо с подтверждением не найдено.")
        return None
    except Exception as e:
        logger.error(f"Ошибка при проверке почты: {str(e)}")
        return None

# Функция для подтверждения почты через ссылку
def confirm_email(confirmation_url):
    try:
        driver = init_driver()
        if driver is None:
            logger.error("WebDriver не был инициализирован.")
            return
        driver.get(confirmation_url)
        time.sleep(2)  # Ждем выполнения перехода
        driver.quit()
        logger.info(f"Почта успешно подтверждена по ссылке: {confirmation_url}")
    except Exception as e:
        logger.error(f"Ошибка при подтверждении почты: {str(e)}")

# Функция для получения кода из письма
def get_code_from_mail(token):
    try:
        url = f"https://api.mail.tm/messages"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Ошибка при получении писем, статус: {response.status_code}")
            return None
        
        messages = response.json()
        for msg in messages:
            if "Ваш код для тестового доступа" in msg['subject']:
                code = msg['text'].split("Ваш тестовый код: ")[1].strip()
                logger.info(f"Получен код для доступа: {code}")
                return code
        logger.info("Код для доступа не найден.")
        return None
    except Exception as e:
        logger.error(f"Ошибка при извлечении кода из письма: {str(e)}")
        return None

# Хэндлер для команды /get
@bot.message_handler(commands=['get'])
def handle_get(message):
    logger.info(f"Пользователь {message.chat.id} запросил код доступа.")
    
    email, token = get_mail()  # Получаем временную почту
    if email is None or token is None:
        bot.send_message(message.chat.id, "Ошибка при получении почты. Попробуйте снова.")
        logger.error(f"Не удалось получить почту для пользователя {message.chat.id}")
        return

    bot.send_message(message.chat.id, f"Используется почта: {email}. Пожалуйста, подождите.")
    logger.info(f"Начинаем процесс отправки почты на сайт для пользователя {message.chat.id}")

    driver = init_driver()
    if driver is None:
        bot.send_message(message.chat.id, "Ошибка при инициализации браузера. Попробуйте позже.")
        logger.error(f"Ошибка при инициализации WebDriver для пользователя {message.chat.id}")
        return

    if submit_email_and_get_code(driver, email):
        bot.send_message(message.chat.id, "Почта успешно отправлена на сайт. Пожалуйста, подтвердите вашу почту.")

        # Проверка почты на наличие письма с подтверждением
        confirmation_url = check_mail_for_confirmation(token)
        if confirmation_url:
            bot.send_message(message.chat.id, "Подтверждаю почту...")
            confirm_email(confirmation_url)

            # Ожидаем письмо с кодом
            bot.send_message(message.chat.id, "Ожидаем код доступа...")
            code = get_code_from_mail(token)
            if code:
                bot.send_message(message.chat.id, f"Ваш код для тестового доступа: {code}")
            else:
                bot.send_message(message.chat.id, "Код не найден.")
        else:
            bot.send_message(message.chat.id, "Не удалось найти письмо с подтверждением.")
            logger.error(f"Не удалось найти письмо с подтверждением для почты {email}")
    else:
        bot.send_message(message.chat.id, "Не удалось отправить почту на сайт.")
        logger.error(f"Не удалось отправить почту на сайт для пользователя {message.chat.id}")
    
    driver.quit()

# Запуск бота
bot.polling()
