import time
import requests
import telebot
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Ваш токен Telegram-бота
TELEGRAM_TOKEN = "7505320830:AAFD9Wt9dvO1vTqPqa4VEvdxZbiDoAjbBqI"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Функция для получения новой временной почты с API Mail.tm
def get_mail():
    response = requests.post('https://api.mail.tm/accounts', json={'address': 'randommail@mail.tm', 'password': 'password123'})
    if response.status_code == 201:
        mail = response.json()
        email = mail['address']
        token = mail['token']
        return email, token
    else:
        return None, None

# Инициализация WebDriver
def init_driver():
    options = Options()
    options.add_argument("--headless")  # Для безголового режима
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Функция для автоматического ввода почты и получения перенаправления
def submit_email_and_get_code(driver, email):
    driver.get("https://hidenx.name/demo/")

    # Находим поле для ввода почты
    email_input = driver.find_element(By.NAME, "email")
    email_input.send_keys(email)
    email_input.send_keys(Keys.RETURN)

    # Ждем перенаправления на success
    time.sleep(3)  # Можно заменить на явные ожидания
    if "success" in driver.current_url:
        return True
    return False

# Функция для проверки почты на наличие письма с подтверждением
def check_mail_for_confirmation(token):
    url = f"https://api.mail.tm/messages"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    messages = response.json()
    
    for msg in messages:
        if "Подтвердите e-mail" in msg['subject']:
            confirmation_url = msg['text']  # Это пример, нужно уточнить, как передается ссылка в тексте письма
            return confirmation_url
    return None

# Функция для подтверждения почты через ссылку
def confirm_email(confirmation_url):
    driver = init_driver()
    driver.get(confirmation_url)
    time.sleep(2)  # Ждем выполнения перехода
    driver.quit()

# Функция для получения кода из письма
def get_code_from_mail(token):
    url = f"https://api.mail.tm/messages"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    messages = response.json()
    
    for msg in messages:
        if "Ваш код для тестового доступа" in msg['subject']:
            code = msg['text'].split("Ваш тестовый код: ")[1].strip()
            return code
    return None

# Хэндлер для команды /get
@bot.message_handler(commands=['get'])
def handle_get(message):
    email, token = get_mail()  # Получаем временную почту
    if email is None or token is None:
        bot.send_message(message.chat.id, "Ошибка при получении почты. Попробуйте снова.")
        return

    bot.send_message(message.chat.id, f"Используется почта: {email}. Пожалуйста, подождите.")

    driver = init_driver()

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
    else:
        bot.send_message(message.chat.id, "Не удалось отправить почту на сайт.")
    
    driver.quit()

# Запуск бота
bot.polling()
