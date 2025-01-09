import logging
from pymailtm import MailTm
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Установим логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка Mail.tm с использованием pymailtm
def create_temp_email():
    # Инициализация клиента с логином и паролем
    client = MailTm(email="your_email@example.com", password="your_password")
    
    # Получаем список доступных доменов
    domains = client.get_domains()
    
    if domains:
        # Используем первый домен из списка
        domain = domains[0]['domain']
        # Создаем временный email
        email = client.create_account(domain=domain)
        return email
    else:
        print("Не удалось получить домены.")
        return None

# Обработчик команды /get в Telegram
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Запрос отправлен. Подождите, пока мы обработаем вашу информацию.")
    
    # Создаем временный email
    email = create_temp_email()
    
    if email:
        await update.message.reply_text(f"Ваш временный email: {email}. Пожалуйста, подождите...")
        
        # Здесь можно добавить код для регистрации на сайте и получения кода
    
    else:
        await update.message.reply_text("Не удалось создать временный email.")

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
