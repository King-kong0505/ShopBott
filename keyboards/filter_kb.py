from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_filter_menu(category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Narx bo'yicha", callback_data=f"filter_price:{category_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🎨 Rang bo'yicha", callback_data=f"filter_color:{category_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📏 O'lcham bo'yicha", callback_data=f"filter_size:{category_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Filterni tozalash", callback_data=f"filter_clear:{category_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"category:{category_id}")
    )
    return builder.as_markup()


def get_color_filter_keyboard(colors: list, category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for color in colors:
        builder.button(
            text=f"🎨 {color}",
            callback_data=f"apply_color:{category_id}:{color}",
        )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"filter:{category_id}"))
    return builder.as_markup()


def get_size_filter_keyboard(sizes: list, category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for size in sizes:
        builder.button(
            text=f"📏 {size}",
            callback_data=f"apply_size:{category_id}:{size}",
        )
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"filter:{category_id}"))
    return builder.as_markup()


def get_cancel_filter_keyboard(category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"filter:{category_id}"))
    return builder.as_markup()
