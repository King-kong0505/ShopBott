from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🛍 Katalog", callback_data="catalog"),
        InlineKeyboardButton(text="🛒 Savatcha", callback_data="cart"),
    )
    builder.row(
        InlineKeyboardButton(text="📦 Buyurtmalarim", callback_data="my_orders"),
        InlineKeyboardButton(text="⭐ Fikr qoldirish", callback_data="feedback_menu"),
    )
    builder.row(
        InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help"),
    )
    return builder.as_markup()


def get_back_to_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))
    return builder.as_markup()
