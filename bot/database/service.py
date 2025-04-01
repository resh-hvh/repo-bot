import os
from aiogram import Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from .models import User, Submission, Base

DATABASE_URL = f"postgresql+asyncpg://admin:1234@localhost:5432/bot_db"

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_user(user_id: int, session: AsyncSession) -> User:
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(user_id=user_id)
        session.add(user)
        await session.commit()
    
    return user

async def create_submission(user_id: int, content_type: str, content: str, media_data: dict = None, session: AsyncSession = None):
    if not session:
        session = async_session()
        submission = Submission(
        user_id=user_id,
        content_type=content_type,
        content=content,
        media_data=media_data
    )
    session.add(submission)
    await session.commit()
    return submission

async def get_admins():
    async with async_session() as session:
        result = await session.execute(select(User).where(User.is_admin == True))
        return result.scalars().all()

async def send_to_admins(bot: Bot, message: Message, content: str, media_data: dict = None):
    admins = await get_admins()
    for admin in admins:
        try:
            if media_data:
                # Логика отправки медиа
                if media_data['content_type'] == 'video_note':
                    await bot.send_video_note(
                        chat_id=admin.user_id,
                        video_note=media_data['file_id']
                    )
                    await bot.send_message(
                        chat_id=admin.user_id,
                        text=f"📹 Видео-сообщение от @{message.from_user.username}\n{content}"
                    )
                else:
                    method = {
                        'photo': bot.send_photo,
                        'video': bot.send_video,
                        'voice': bot.send_voice
                    }[media_data['content_type']]
                    
                    await method(
                        chat_id=admin.user_id,
                        **{media_data['content_type']: media_data['file_id']},
                        caption=content
                    )
            else:
                # Отправка текста
                await bot.send_message(
                    chat_id=admin.user_id,
                    text=f"📨 Новое предложение от @{message.from_user.username}:\n{content}"
                )
                
        except Exception as e:
            print(f"Ошибка отправки админу {admin.user_id}: {str(e)}")

async def get_submissions(page: int = 1, per_page: int = 5):
    async with async_session() as session:
        offset = (page - 1) * per_page
        result = await session.execute(
            select(Submission)
            .order_by(Submission.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        return result.scalars().all()

async def get_total_submissions():
    async with async_session() as session:
        result = await session.execute(select(func.count(Submission.id)))
        return result.scalar()

async def get_submission_by_index(index: int) -> Submission | None:
    async with async_session() as session:
        result = await session.execute(
            select(Submission)
            .order_by(Submission.created_at.desc())
            .offset(index)
            .limit(1)
        )
        return result.scalars().first()

async def get_total_submissions_count() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(Submission.id)))
        return result.scalar() or 0