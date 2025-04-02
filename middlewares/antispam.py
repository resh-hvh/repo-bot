from datetime import datetime, timedelta
from aiogram.types import Message
from aiogram.filters import Command
from database.service import get_user

class AntispamMiddleware:
    async def __call__(self, handler, event: Message, data):
        # Проверяем, что это команда /send
        if not event.text or not event.text.startswith('/send'):
            return await handler(event, data)
            
        session = data["session"]
        user = await get_user(event.from_user.id, session)
        
        if user.last_request and (datetime.now() - user.last_request) < timedelta(seconds=4):
            await event.answer("⏳ Подождите 5 минут перед следующей отправкой")
            return
        
        response = await handler(event, data)
        user.last_request = datetime.now()
        await session.commit()
        return response