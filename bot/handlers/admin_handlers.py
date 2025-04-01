from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Submission, User
from database.service import get_submission_by_index, get_total_submissions_count, get_user, get_submissions, get_total_submissions, async_session
from keyboards.pagination import PaginationKeyboard

router = Router()

class AddAdmin(StatesGroup):
    waiting_for_user_id = State()

async def edit_or_resend_message(
    bot: Bot,
    chat_id: int,
    message_id: int,
    submission: Submission,
    index: int,
    total: int
) -> int:
    keyboard = PaginationKeyboard(index, total).get_markup()
    
    try:
        # Всегда проверяем наличие медиа данных
        if not submission.media_data or not submission.media_data.get('file_id'):
            return await send_new_media(bot, chat_id, submission, keyboard)
            
        return await send_new_media(bot, chat_id, submission, keyboard)
        
    except Exception as e:
        error_msg = await bot.send_message(chat_id, f"⚠️ Ошибка: {str(e)}")
        return error_msg.message_id
    
async def send_new_media(bot: Bot, chat_id: int, submission: Submission, keyboard) -> int:
    try:
        # Всегда проверяем наличие media_data
        media_data = submission.media_data or {}
        content_type = media_data.get('content_type')
        file_id = media_data.get('file_id')
        
        caption = f"#{submission.id}"
        if submission.content:
            caption += f"\n{submission.content}"

        match content_type:
            case 'photo':
                msg = await bot.send_photo(
                    chat_id=chat_id,
                    photo=file_id,
                    caption=caption,
                    reply_markup=keyboard
                )
            case 'video':
                msg = await bot.send_video(
                    chat_id=chat_id,
                    video=file_id,
                    caption=caption,
                    reply_markup=keyboard
                )
            case 'voice':
                msg = await bot.send_voice(
                    chat_id=chat_id,
                    voice=file_id,
                    caption=caption,
                    reply_markup=keyboard
                )
            case 'video_note':
                msg = await bot.send_video_note(
                    chat_id=chat_id,
                    video_note=file_id
                )
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    reply_markup=keyboard
                )
            case _:  # Для текстовых сообщений
                msg = await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    reply_markup=keyboard
                )
        return msg.message_id
        
    except Exception as e:
        error_msg = await bot.send_message(chat_id, f"⚠️ Ошибка: {str(e)}")
        return error_msg.message_id

async def download_and_send(bot: Bot, chat_id: int, submission: Submission, index: int, total: int):
    try:
        # Проверка наличия file_id
        if 'file_id' not in submission.media_data:
            raise ValueError("Отсутствует file_id в медиа-данных")
            
        keyboard = PaginationKeyboard(index, total).get_markup()
        file = await bot.get_file(submission.media_data['file_id'])
        video_data = await bot.download_file(file.file_path)
        
        msg = await bot.send_video(
            chat_id=chat_id,
            video=BufferedInputFile(video_data.read(), filename="video_note.mp4"),
            caption=f"📹 Видео-сообщение (#{submission.id})",
            reply_markup=keyboard
        )
        
        return [msg.message_id]
        
    except Exception as e:
        error_msg = await bot.send_message(chat_id, f"❌ Ошибка конвертации: {str(e)}")
        return [error_msg.message_id]


@router.message(Command("add"))
async def add_admin_start(message: Message, state: FSMContext, session: AsyncSession):
    # Получаем сессию из контекста
    user = await get_user(message.from_user.id, session)  # Передаем сессию
    
    if user.is_admin:
        await message.answer("🔢 Введите ID нового админа:")
        await state.set_state(AddAdmin.waiting_for_user_id)
    else:
        await message.answer("⛔ У вас нет прав для этой команды")

@router.message(AddAdmin.waiting_for_user_id)
async def add_admin_finish(message: Message, state: FSMContext):
    try:
        new_admin_id = int(message.text)
        async with async_session() as session:
            # Получаем пользователя в рамках текущей сессии
            user = await session.get(User, new_admin_id)
            
            if not user:
                # Создаем нового администратора
                user = User(user_id=new_admin_id, is_admin=True)
                session.add(user)
            else:
                # Обновляем существующего пользователя
                user.is_admin = True
                
            await session.commit()
            await message.answer(f"✅ Пользователь {new_admin_id} стал администратором")
            
    except ValueError:
        await message.answer("❌ Некорректный ID")
    finally:
        await state.clear()
        
async def send_submission_message(bot: Bot, chat_id: int, submission: Submission, index: int, total: int, last_messages: list):
    keyboard = PaginationKeyboard(index, total).get_markup()
    content = submission.content or "🖼️ Медиа-контент"
    total = await get_total_submissions_count()

    for msg_id in last_messages:
        try:
            await bot.delete_message(chat_id, msg_id)
        except:
            pass

    messages = []
    

    try:
        if submission.media_data and submission.media_data.get('file_id'):
            match submission.content_type:
                case 'photo':
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=submission.media_data['file_id'],
                        caption=f"#{submission.id}\n{content}",
                        reply_markup=keyboard
                    )
                case 'video':
                    await bot.send_video(
                        chat_id=chat_id,
                        video=submission.media_data['file_id'],
                        caption=f"#{submission.id}\n{content}",
                        reply_markup=keyboard
                    )
                case 'voice':
                    await bot.send_voice(
                        chat_id=chat_id,
                        voice=submission.media_data['file_id'],
                        caption=f"#{submission.id}\n{content}",
                        reply_markup=keyboard
                    )
        else:
            msg = await bot.send_message(
                chat_id=chat_id,
                text=f"#{submission.id}\n{content}",
                reply_markup=keyboard
            )
            messages = [msg.message_id]
        return messages
    except Exception as e:
        await bot.send_message(
            chat_id=chat_id,
            text=f"Ошибка отображения сообщения #{submission.id}:\n{str(e)}"
        )


@router.message(Command("moderate"))
async def start_moderation(message: Message, bot: Bot, state: FSMContext):
    total = await get_total_submissions_count()
    if total == 0:
        return await message.answer("📭 Нет сообщений для модерации")
    
    submission = await get_submission_by_index(0)
    message_id = await send_new_media(bot, message.chat.id, submission, PaginationKeyboard(0, total).get_markup())
    
    await state.update_data(
        current_index=0,
        last_message_id=message_id
    )

@router.callback_query(F.data.startswith(("prev_", "next_")))
async def handle_pagination(callback: CallbackQuery, bot: Bot, state: FSMContext):
    try:
        data = await state.get_data()
        current_index = data.get("current_index", 0)
        total = await get_total_submissions_count()
        
        # Определяем новую позицию
        new_index = current_index - 1 if "prev" in callback.data else current_index + 1
        new_index = max(0, min(new_index, total - 1))
        
        submission = await get_submission_by_index(new_index)
        if not submission:
            await callback.answer("❌ Сообщение не найдено")
            return
        
        # Обновляем сообщение
        new_message_id = await edit_or_resend_message(
            bot=bot,
            chat_id=callback.message.chat.id,
            message_id=data["last_message_id"],
            submission=submission,
            index=new_index,
            total=total
        )
        
        await state.update_data(
            current_index=new_index,
            last_message_id=new_message_id
        )
        await callback.answer()

    except Exception as e:
        await callback.answer(f"⚠️ Ошибка: {str(e)}")

# @router.callback_query(F.data.startswith(("prev_", "next_")))
# async def handle_pagination(callback: CallbackQuery, bot: Bot, state: FSMContext):
#     try:
#         action, index_str = callback.data.split("_")
#         current_index = int(index_str)
#         total = await get_total_submissions_count()

#         # Проверка валидности индекса
#         if current_index < 0 or current_index >= total:
#             await callback.answer("❌ Неверная страница")
#             return

#         # Получаем данные состояния
#         data = await state.get_data()
#         last_messages = data.get("last_messages", [])

#         # Удаляем предыдущие сообщения
#         for msg_id in last_messages:
#             try:
#                 await bot.delete_message(callback.message.chat.id, msg_id)
#             except:
#                 pass

#         # Получаем и отправляем новое сообщение
#         submission = await get_submission_by_index(current_index)
#         if submission:
#             messages = await send_submission_message(bot, callback.message.chat.id, submission, current_index, total)
#             await state.update_data(last_messages=messages)
        
#         await callback.answer()
        
#     except Exception as e:
#         await callback.answer(f"⚠️ Ошибка: {str(e)}")