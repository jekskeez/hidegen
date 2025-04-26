import os
import asyncio
import json
import random
import string
import time
import re
import logging
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import CommandHandler, ApplicationBuilder
from bs4 import BeautifulSoup
from pymailtm import MailTm
import requests

# Настройка логирования
LOG_FILE = "bot.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
CONFIG_FILE = "config.json"

def log_command(func):
    """Декоратор для логирования команд"""
    async def wrapper(update: Update, context):
        user = update.effective_user
        logger.info(f"User {user.id} ({user.full_name}) вызвал команду /{func.__name__}")
        try:
            return await func(update, context)
        except Exception as e:
            logger.error(f"Ошибка в команде /{func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper

def load_config():
    """Загружает конфигурацию из файла"""
    default_config = {"base_url": "https://hidenx.name"}
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            if "base_url" not in config:
                save_config(default_config)
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        save_config(default_config)
        return default_config

def save_config(config):
    """Сохраняет конфигурацию в файл"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Инициализация конфига
config = load_config()
demo_url = f"{config['base_url'].rstrip('/')}/demo/"

# Настройка MailTM
os.makedirs(os.path.expanduser("~/.pymailtm"), exist_ok=True)
mail_client = MailTm()

def generate_username(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_available_domains():
    try:
        logger.debug("Запрос списка доменов Mail.tm")
        response = requests.get("https://api.mail.tm/domains")
        if response.status_code == 200:
            domains = [domain['domain'] for domain in response.json()['hydra:member']]
            logger.debug(f"Получено {len(domains)} доменов")
            return domains
        logger.error(f"Ошибка при получении доменов. Код: {response.status_code}")
        return []
    except Exception as e:
        logger.error("Ошибка при получении доменов", exc_info=True)
        return []

def create_email():
    try:
        logger.info("Создание нового email-адреса")
        domains = get_available_domains()
        
        if not domains:
            logger.error("Нет доступных доменов для регистрации")
            return None
        
        domain = domains[0]
        username = generate_username()
        address = f"{username}@{domain}"
        password = generate_username(12)

        logger.debug(f"Попытка регистрации аккаунта: {address}")
        response = requests.post("https://api.mail.tm/accounts", json={
            "address": address,
            "password": password
        })
        
        if response.status_code == 201:
            logger.info(f"Успешная регистрация: {address}")
            return (address, password)
        logger.error(f"Ошибка регистрации: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        logger.error("Ошибка при создании почты", exc_info=True)
        return None

def get_token(email, password):
    try:
        logger.debug(f"Получение токена для {email}")
        response = requests.post("https://api.mail.tm/token", json={"address": email, "password": password})
        if response.status_code == 200:
            return response.json().get("token")
        logger.error(f"Ошибка авторизации: {response.status_code}")
        return None
    except Exception as e:
        logger.error("Ошибка при запросе токена", exc_info=True)
        return None

def get_inbox(email, password, retries=20, delay=10):
    token = get_token(email, password)
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(retries):
        logger.debug(f"Попытка {attempt+1}/{retries} получения писем")
        response = requests.get("https://api.mail.tm/messages", headers=headers)
        if response.status_code == 200 and (messages := response.json().get("hydra:member")):
            logger.info(f"Получено {len(messages)} писем")
            return messages
        time.sleep(delay)
    logger.warning("Не удалось получить письма")
    return []

def register_on_site(email):
    try:
        logger.info(f"Начало регистрации для {email}")
        session = requests.Session()
        
        def load_page(url):
            logger.debug(f"Загрузка страницы: {url}")
            response = session.get(url)
            if response.status_code != 200:
                logger.warning(f"Ошибка загрузки {url} - код {response.status_code}")
                return None
            return BeautifulSoup(response.text, 'html.parser')

        soup = load_page(demo_url)
        if not soup:
            return None

        def find_email_field(soup):
            return soup.find('input', {'name': 'demo_mail'})

        email_field = find_email_field(soup)
        if not email_field:
            reset_url = f"{demo_url}reset/"
            logger.warning("Поле email не найдено, попытка сброса")
            if not load_page(reset_url):
                return None
            soup = load_page(demo_url)

        if not (email_field := find_email_field(soup)):
            logger.error("Поле email не найдено после сброса")
            return None

        hidden_inputs = soup.find_all('input', type='hidden')
        form_data = {input['name']: input.get('value', '') for input in hidden_inputs}
        form_data['demo_mail'] = email

        logger.debug("Отправка формы регистрации")
        response = session.post(demo_url, data=form_data)
        if response.status_code == 200:
            title_text = BeautifulSoup(response.text, 'html.parser').find('title').get_text(strip=True)
            if "Ваш код выслан на почту" in title_text:
                logger.info(f"Успешная регистрация для {email}")
                return email
            logger.warning(f"Неожиданный ответ сервера: {title_text}")
            return None
        logger.error(f"Ошибка регистрации: {response.status_code}")
        return None
    except Exception as e:
        logger.error("Ошибка при регистрации", exc_info=True)
        return None

def confirm_email(email, password):
    try:
        logger.info(f"Подтверждение почты {email}")
        if not (token := get_token(email, password)):
            return False

        headers = {"Authorization": f"Bearer {token}"}
        session = requests.Session()

        for attempt in range(20):
            logger.debug(f"Попытка {attempt+1}/20 подтверждения")
            response = requests.get("https://api.mail.tm/messages", headers=headers)
            if response.status_code == 200:
                for message in response.json().get("hydra:member", []):
                    email_response = requests.get(f"https://api.mail.tm/messages/{message['id']}", headers=headers)
                    if email_response.status_code == 200:
                        html_body = email_response.json().get("html", [""])[0]
                        soup = BeautifulSoup(html_body, "html.parser")
                        for link in soup.find_all("a", href=re.compile(r"^https://hidemy\.esclick\.me/")):
                            if link.find_parent("span") and "Подтвердить" in link.find_parent("span").text:
                                logger.info("Найдена ссылка подтверждения")
                                confirm_response = session.get(link["href"])
                                if confirm_response.status_code == 200:
                                    logger.info("Почта успешно подтверждена")
                                    return True
            time.sleep(8)
        logger.warning("Не удалось подтвердить почту")
        return False
    except Exception as e:
        logger.error("Ошибка при подтверждении почты", exc_info=True)
        return False

def get_test_code(email, password):
    try:
        logger.info(f"Поиск тестового кода для {email}")
        if not (token := get_token(email, password)):
            return None

        headers = {"Authorization": f"Bearer {token}"}
        for attempt in range(20):
            logger.debug(f"Попытка {attempt+1}/20 получения кода")
            response = requests.get("https://api.mail.tm/messages", headers=headers)
            if response.status_code == 200:
                for message in response.json().get("hydra:member", []):
                    if "Ваш код для тестового доступа к сервису" in message.get("subject", ""):
                        email_response = requests.get(f"https://api.mail.tm/messages/{message['id']}", headers=headers)
                        if email_response.status_code == 200:
                            code = email_response.json().get("intro", "").split(":")[1].strip()
                            logger.info(f"Найден тестовый код: {code}")
                            return code
            time.sleep(8)
        logger.warning("Тестовый код не найден")
        return None
    except Exception as e:
        logger.error("Ошибка при получении тестового кода", exc_info=True)
        return None

@log_command
async def start(update: Update, context):
    await update.message.reply_text("Привет! Я могу регистрировать тестовые коды для hidemyname VPN. Отправь /get для получения кода.")

@log_command
async def get_test_code_telegram(update: Update, context):
    try:
        logger.info("Обработка команды /get")
        await update.message.reply_text("Ваш код будет готов примерно через 2 минуты. Пожалуйста, подождите...")
        
        if not (creds := create_email()):
            await update.message.reply_text("Ошибка при создании почты. Попробуйте позже.")
            return

        email, password = creds
        logger.info(f"Создана почта: {email}")
        
        await update.message.reply_text(
            f"Почта: {email}\nПароль: {password}\n"
            f"Проверить почту: https://mail.tm/"
        )

        if not (register_on_site(email) and confirm_email(email, password)):
            logger.error("Ошибка регистрации/подтверждения")
            await update.message.reply_text("Ошибка в процессе регистрации")
            return

        if test_code := get_test_code(email, password):
            logger.info(f"Успешно получен код для {email}")
            await update.message.reply_text(f"Ваш тестовый код: {test_code}")
        else:
            logger.warning("Не удалось получить код")
            await update.message.reply_text("Не удалось получить код")
    except Exception as e:
        logger.error("Критическая ошибка в /get", exc_info=True)
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

@log_command
async def set_url(update: Update, context):
    try:
        if not context.args:
            await update.message.reply_text("Используйте: /set https://ваш.домен")
            return

        new_url = context.args[0].strip()
        logger.info(f"Попытка установки URL: {new_url}")

        try:
            parsed = urlparse(new_url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError
        except:
            logger.warning("Некорректный URL")
            await update.message.reply_text("❌ Некорректный URL! Пример: https://example.com")
            return

        global demo_url
        config.update({"base_url": new_url.rstrip('/')})
        save_config(config)
        demo_url = f"{config['base_url']}/demo/"
        
        logger.info("URL успешно обновлен")
        await update.message.reply_text(f"✅ URL обновлен!\nНовый адрес: {demo_url}")
    except Exception as e:
        logger.error("Ошибка в команде /set", exc_info=True)
        await update.message.reply_text("❌ Ошибка при обновлении URL")

def main():
    logger.info("Запуск бота")
    try:
        application = ApplicationBuilder().token('7505320830:AAFa_2WvRVEo_I1YkiO-RQDS2FwGtLJY1po').build()
        application.add_handlers([
            CommandHandler("start", start),
            CommandHandler("get", get_test_code_telegram),
            CommandHandler("set", set_url)
        ])
        application.run_polling()
    except Exception as e:
        logger.critical("Фатальная ошибка при запуске бота", exc_info=True)
    finally:
        logger.info("Остановка бота")

if __name__ == '__main__':
    asyncio.run(main())
