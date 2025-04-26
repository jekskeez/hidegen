import logging
from datetime import datetime
# ... остальные импорты остаются без изменений ...

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

# Модифицируем функции логирования
def get_available_domains():
    try:
        logger.debug("Запрос списка доменов Mail.tm")
        response = requests.get("https://api.mail.tm/domains")
        if response.status_code == 200:
            logger.debug(f"Получено {len(response.json()['hydra:member'])} доменов")
            return [domain['domain'] for domain in response.json()['hydra:member']]
        else:
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
        else:
            logger.error(f"Ошибка регистрации: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error("Ошибка при создании почты", exc_info=True)
        return None

# Аналогично модифицируем все остальные функции, заменяя print на logger
# Например в функции register_on_site:
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
        # ... остальная часть функции ...

# Модифицируем обработчики команд
@log_command
async def start(update: Update, context):
    await update.message.reply_text("Привет! Я могу регистрировать тестовые коды для hidemyname VPN. Отправь /get для получения кода.")

@log_command
async def get_test_code_telegram(update: Update, context):
    try:
        logger.info("Начало обработки команды /get")
        await update.message.reply_text("Ваш код будет готов примерно через 2 минуты. Пожалуйста, подождите...")
        
        if not (creds := create_email()):
            await update.message.reply_text("Ошибка при создании почты. Попробуйте позже.")
            return

        email, password = creds
        logger.info(f"Создана новая почта: {email}")
        
        await update.message.reply_text(
            f"Почта: {email}\nПароль: {password}\n"
            f"Проверить почту: https://mail.tm/"
        )

        if not (register_on_site(email) and confirm_email(email, password)):
            logger.error("Ошибка в процессе регистрации")
            await update.message.reply_text("Ошибка в процессе регистрации")
            return

        if test_code := get_test_code(email, password):
            logger.info(f"Успешно получен код для {email}")
            await update.message.reply_text(f"Ваш тестовый код: {test_code}")
        else:
            logger.warning(f"Не удалось получить код для {email}")
            await update.message.reply_text("Не удалось получить код")
    except Exception as e:
        logger.error("Критическая ошибка в /get", exc_info=True)
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

# Остальные функции модифицируются аналогично

def main():
    logger.info("Запуск бота")
    try:
        application = ApplicationBuilder().token('YOUR_TOKEN').build()
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
