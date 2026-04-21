from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = os.getenv('BOT_TOKEN', '')
    admin_id: int = int(os.getenv('ADMIN_ID', '0'))
    channel_id: int = int(os.getenv('CHANNEL_ID', '0'))
    channel_link: str = os.getenv('CHANNEL_LINK', '')
    database_path: str = os.getenv('DATABASE_PATH', 'nail_bot.db')
    timezone: str = os.getenv('TIMEZONE', 'Europe/Moscow')


config = Config()

if not config.bot_token:
    raise ValueError('BOT_TOKEN не найден в переменных окружения.')
if not config.admin_id:
    raise ValueError('ADMIN_ID не найден в переменных окружения.')
if not config.channel_id:
    raise ValueError('CHANNEL_ID не найден в переменных окружения.')
if not config.channel_link:
    raise ValueError('CHANNEL_LINK не найден в переменных окружения.')
