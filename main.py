import asyncio
import os
from src import TelegramBot
from dotenv import load_dotenv

load_dotenv()

def main():
    token = os.getenv('TOKEN')
    chat_id = os.getenv('CHAT_ID')
    server_name = os.getenv('SERVER_NAME')
    partitions = os.getenv('PARTITIONS').split(', ')
    language = os.getenv('LANGUAGE', 'en')

    bot = TelegramBot(token, chat_id, server_name, partitions, language)
    asyncio.run(bot.send_message())

if __name__ == '__main__':
    main()
