from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_cart_keyboard(cart_items: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in cart_items:
        builder.row(
            InlineKeyboardButton(
                text=f"❌ {item['name']} ({item.get('size','')}, {item.get('color','')})",
                callback_data=f"rm_cart:{item['id']}",
            )
        )
    if cart_items:
        builder.row(
            InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="checkout"),
            InlineKeyboardButton(text="🗑 Tozalash", callback_data="clear_cart"),
        )
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))
    return builder.as_markup()


def get_checkout_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cart"),
    )
    return builder.as_markup()


def get_order_done_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📦 Buyurtmalarim", callback_data="my_orders"))
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))
    return builder.as_markup()


def get_cancel_keyboard(back_to: str = "main_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data=back_to))
    return builder.as_markup()
