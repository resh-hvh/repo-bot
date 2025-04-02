from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class PaginationKeyboard:
    def __init__(self, current_index: int, total: int):
        self.current_index = current_index
        self.total = total

    def get_markup(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        # Кнопки становятся неактивными у границ
        builder.row(
            InlineKeyboardButton(
                text="←", 
                callback_data=f"prev_{self.current_index-1}",
                disabled=self.current_index <= 0
            ),
            InlineKeyboardButton(
                text=f"{self.current_index+1}/{self.total}", 
                callback_data="current"
            ),
            InlineKeyboardButton(
                text="→", 
                callback_data=f"next_{self.current_index+1}",
                disabled=self.current_index >= self.total-1
            )
        )
        return builder.as_markup()