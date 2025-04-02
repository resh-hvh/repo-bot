from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from database.service import create_submission, send_to_admins

router = Router()

class SendMessage(StatesGroup):
    waiting_for_content = State()

@router.message(Command("get_id"))
async def get_id(message: Message):
    await message.answer(f"Ваш уникальный ID: {message.from_user.id}")

@router.message(Command("start"))
async def start(message: Message):
    await message.answer("👋 Привет! Отправляйте ваши предложения через /send")
    await message.answer(f"{message.from_user.id}")

@router.message(Command("send"))
async def send_start(message: Message, state: FSMContext):
    await message.answer("📤 Отправьте ваш контент:")
    await state.set_state(SendMessage.waiting_for_content)

@router.message(SendMessage.waiting_for_content)
async def handle_content(message: Message, state: FSMContext, bot: Bot):
    try:
        content_type = message.content_type
        content = message.text or message.caption or ""
        media_data = {}  # Всегда инициализируем словарь

        if content_type == ContentType.VIDEO_NOTE:
            media_data = {
                'file_id': message.video_note.file_id,
                'content_type': 'video_note'
            }
        elif content_type == ContentType.PHOTO:
            file = await bot.get_file(message.photo[-1].file_id)
            path = file.file_path
            print(f"https://api.telegram.org/file/bot7563912668:AAGBOQCPSBj7VU-INimUQtTYEseV29Ho_60/{path}")
            media_data = {
                'file_id': message.photo[-1].file_id,
                'content_type': 'photo'
            }
        elif content_type == ContentType.VIDEO:
            media_data = {
                'file_id': message.video.file_id,
                'content_type': 'video'
            }
        elif content_type == ContentType.VOICE:
            media_data = {
                'file_id': message.voice.file_id,
                'content_type': 'voice'
            }

        await create_submission(
            user_id=message.from_user.id,
            content_type=content_type,
            content=content,
            media_data=media_data if media_data else None
        )
        
        await send_to_admins(bot, message, content, media_data)
        await message.answer("✅ Сообщение отправлено!")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    finally:
        await state.clear()