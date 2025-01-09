import asyncio
from mailtm import EmailClient

async def create_and_check_email():
    """Создает почту, проверяет входящие письма и выводит их содержимое."""
    try:
        # Создаем клиента
        client = EmailClient()
        await client.connect()
        
        # Регистрируем новую почту
        account = await client.register()
        print(f"Создана почта: {account.address}")

        # Проверяем входящие письма
        print("Ожидание письма...")
        while True:
            messages = await account.get_messages()
            if messages:
                for message in messages:
                    print(f"Найдено письмо: {message['subject']}")
                    # Получаем содержимое письма
                    message_details = await account.get_message(message['id'])
                    print(f"Содержимое письма: {message_details['text']}")
                break
            await asyncio.sleep(5)  # Ожидание перед повторной проверкой
    except Exception as e:
        print(f"Ошибка: {e}")

async def main():
    await create_and_check_email()

# Запуск программы
asyncio.run(main())
