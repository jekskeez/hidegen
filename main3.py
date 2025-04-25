import os
import asyncio
import json
import random
import string
import time
import re
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import CommandHandler, ApplicationBuilder
from bs4 import BeautifulSoup
from pymailtm import MailTm
import requests

# Конфигурация
CONFIG_FILE = "config.json"

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
        response = requests.get("https://api.mail.tm/domains")
        return [domain['domain'] for domain in response.json()['hydra:member']] if response.status_code == 200 else []
    except Exception as e:
        print(f"Ошибка при получении доменов: {e}")
        return []

def create_email():
    try:
        domains = get_available_domains()
        if not domains:
            return None
        
        domain = domains[0]
        username = generate_username()
        address = f"{username}@{domain}"
        password = generate_username(12)

        response = requests.post("https://api.mail.tm/accounts", json={
            "address": address,
            "password": password
        })
        
        return (address, password) if response.status_code == 201 else None
    except Exception as e:
        print(f"Ошибка при создании почты: {e}")
        return None

def get_token(email, password):
    try:
        response = requests.post("https://api.mail.tm/token", json={"address": email, "password": password})
        return response.json().get("token") if response.status_code == 200 else None
    except Exception as e:
        print(f"Ошибка при запросе токена: {e}")
        return None

def get_inbox(email, password, retries=20, delay=10):
    token = get_token(email, password)
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(retries):
        response = requests.get("https://api.mail.tm/messages", headers=headers)
        if response.status_code == 200 and (messages := response.json().get("hydra:member")):
            return messages
        time.sleep(delay)
    return []

def register_on_site(email):
    try:
        session = requests.Session()
        
        def load_page(url):
            response = session.get(url)
            return BeautifulSoup(response.text, 'html.parser') if response.status_code == 200 else None

        soup = load_page(demo_url)
        if not soup:
            return None

        def find_email_field(soup):
            return soup.find('input', {'name': 'demo_mail'})

        email_field = find_email_field(soup)
        if not email_field:
            reset_url = f"{demo_url}reset/"
            if not load_page(reset_url):
                return None
            soup = load_page(demo_url)

        if not (email_field := find_email_field(soup)):
            return None

        hidden_inputs = soup.find_all('input', type='hidden')
        form_data = {input['name']: input.get('value', '') for input in hidden_inputs}
        form_data['demo_mail'] = email

        response = session.post(demo_url, data=form_data)
        if response.status_code == 200:
            title_text = BeautifulSoup(response.text, 'html.parser').find('title').get_text(strip=True)
            return email if "Ваш код выслан на почту" in title_text else None
        return None
    except Exception as e:
        print(f"Ошибка при регистрации: {e}")
        return None

def confirm_email(email, password):
    try:
        if not (token := get_token(email, password)):
            return False

        headers = {"Authorization": f"Bearer {token}"}
        session = requests.Session()

        for _ in range(20):
            response = requests.get("https://api.mail.tm/messages", headers=headers)
            if response.status_code == 200:
                for message in response.json().get("hydra:member", []):
                    email_response = requests.get(f"https://api.mail.tm/messages/{message['id']}", headers=headers)
                    if email_response.status_code == 200:
                        html_body = email_response.json().get("html", [""])[0]
                        soup = BeautifulSoup(html_body, "html.parser")
                        for link in soup.find_all("a", href=re.compile(r"^https://hidemy\.esclick\.me/")):
                            if link.find_parent("span") and "Подтвердить" in link.find_parent("span").text:
                                confirm_response = session.get(link["href"])
                                if confirm_response.status_code == 200:
                                    return True
            time.sleep(8)
        return False
    except Exception as e:
        print(f"Ошибка при подтверждении почты: {e}")
        return False

def get_test_code(email, password):
    try:
        if not (token := get_token(email, password)):
            return None

        headers = {"Authorization": f"Bearer {token}"}
        for _ in range(20):
            response = requests.get("https://api.mail.tm/messages", headers=headers)
            if response.status_code == 200:
                for message in response.json().get("hydra:member", []):
                    if "Ваш код для тестового доступа к сервису" in message.get("subject", ""):
                        email_response = requests.get(f"https://api.mail.tm/messages/{message['id']}", headers=headers)
                        return email_response.json().get("intro", "").split(":")[1].strip() if email_response.status_code == 200 else None
            time.sleep(8)
        return None
    except Exception as e:
        print(f"Ошибка при получении тестового кода: {e}")
        return None

async def start(update: Update, context):
    await update.message.reply_text("Привет! Я могу регистрировать тестовые коды для hidemyname VPN. Отправь /get для получения кода.")

async def get_test_code_telegram(update: Update, context):
    try:
        await update.message.reply_text("Ваш код будет готов примерно через 2 минуты. Пожалуйста, подождите...")
        
        if not (creds := create_email()):
            await update.message.reply_text("Ошибка при создании почты. Попробуйте позже.")
            return

        email, password = creds
        await update.message.reply_text(
            f"Почта: {email}\nПароль: {password}\n"
            f"Проверить почту: https://mail.tm/"
        )

        if not (register_on_site(email) and confirm_email(email, password)):
            await update.message.reply_text("Ошибка в процессе регистрации")
            return

        if test_code := get_test_code(email, password):
            await update.message.reply_text(f"Ваш тестовый код: {test_code}")
        else:
            await update.message.reply_text("Не удалось получить код")
    except Exception as e:
        print(f"Ошибка: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

async def set_url(update: Update, context):
    if not context.args:
        await update.message.reply_text("Используйте: /set https://ваш.домен")
        return

    new_url = context.args[0].strip()
    try:
        parsed = urlparse(new_url)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError
    except:
        await update.message.reply_text("❌ Некорректный URL! Пример: https://example.com")
        return

    global demo_url
    config.update({"base_url": new_url.rstrip('/')})
    save_config(config)
    demo_url = f"{config['base_url']}/demo/"
    
    await update.message.reply_text(f"✅ URL обновлен!\nНовый адрес: {demo_url}")

def main():
    application = ApplicationBuilder().token('7505320830:AAFa_2WvRVEo_I1YkiO-RQDS2FwGtLJY1po').build()
    application.add_handlers([
        CommandHandler("start", start),
        CommandHandler("get", get_test_code_telegram),
        CommandHandler("set", set_url)
    ])
    application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
