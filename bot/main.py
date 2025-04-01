import os
import asyncio
from aiogram import Bot, Dispatcher
from middlewares.antispam import AntispamMiddleware
from database.middleware import DbSessionMiddleware
from handlers import admin_handlers, user_handlers
from database.service import create_tables

async def main():
    await create_tables()
    bot = Bot(token="7563912668:AAGBOQCPSBj7VU-INimUQtTYEseV29Ho_60")
    dp = Dispatcher()
    
    dp.update.middleware(DbSessionMiddleware())
    user_handlers.router.message.middleware(AntispamMiddleware())
    admin_handlers.router.message.middleware(DbSessionMiddleware())
    user_handlers.router.message.middleware(DbSessionMiddleware())

    
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())