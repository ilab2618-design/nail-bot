import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from database.db import Database
from handlers.admin import router as admin_router
from handlers.user import router as user_router
from services.scheduler import restore_scheduler_jobs, scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    db = Database(config.database_path)
    await db.init()

    dp['db'] = db
    dp.include_router(user_router)
    dp.include_router(admin_router)

    scheduler.start()
    await restore_scheduler_jobs(bot, db, config.timezone)

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
