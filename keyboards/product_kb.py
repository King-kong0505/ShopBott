from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_product_keyboard(product: dict, category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if product["stock"] > 0:
        builder.row(
            InlineKeyboardButton(
                text="🛒 Savatchaga qo'shish",
                callback_data=f"choose_size:{product['id']}:{category_id}",
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(text="❌ Stokda yo'q", callback_data="noop")
        )

    builder.row(
        InlineKeyboardButton(
            text="📞 Sotuvchi bilan bog'lanish",
            callback_data=f"contact_seller:{product['id']}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⭐ Fikrlarni ko'rish",
            callback_data=f"view_feedback:{product['id']}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data=f"category:{category_id}",
        )
    )
    return builder.as_markup()


def get_size_keyboard(product: dict, category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for size in product.get("sizes", []):
        builder.button(
            text=f"📏 {size}",
            callback_data=f"sel_size:{product['id']}:{category_id}:{size}",
        )
    builder.adjust(3)
    builder.row(
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data=f"product:{product['id']}:{category_id}",
        )
    )
    return builder.as_markup()


def get_color_keyboard(product: dict, category_id: int, selected_size: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for color in product.get("colors", []):
        builder.button(
            text=f"🎨 {color}",
            callback_data=f"sel_color:{product['id']}:{category_id}:{selected_size}:{color}",
        )
    builder.adjust(3)
    builder.row(
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data=f"choose_size:{product['id']}:{category_id}",
        )
    )
    return builder.as_markup()


def get_confirm_add_keyboard(product_id: int, category_id: int, size: str, color: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Savatchaga qo'shish",
            callback_data=f"add_cart:{product_id}:{category_id}:{size}:{color}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data=f"product:{product_id}:{category_id}",
        )
    )
    return builder.as_markup()


def get_feedback_list_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔙 Mahsulotga qaytish",
            callback_data=f"product:{product_id}:{category_id}",
        )
    )
    return builder.as_markup()
