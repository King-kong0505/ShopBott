import math
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ITEMS_PER_PAGE


def get_categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"{cat['emoji']} {cat['name']}",
                callback_data=f"category:{cat['id']}",
            )
        )
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))
    return builder.as_markup()


def get_products_keyboard(
    products: list,
    total: int,
    current_page: int,
    category_id: int,
    min_price: float = 0,
    max_price: float = 0,
    color: str = "",
    size: str = "",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for p in products:
        stock_icon = "❌" if p["stock"] <= 0 else "✅"
        price_fmt = f"{p['price']:,.0f}".replace(",", " ")
        label = f"{stock_icon} {p['name']} — {price_fmt} so'm"
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=f"product:{p['id']}:{category_id}",
            )
        )

    total_pages = max(1, math.ceil(total / ITEMS_PER_PAGE))
    nav = []
    if current_page > 1:
        nav.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"page:{category_id}:{current_page-1}:{min_price}:{max_price}:{color}:{size}",
            )
        )
    nav.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="noop"))
    if current_page < total_pages:
        nav.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"page:{category_id}:{current_page+1}:{min_price}:{max_price}:{color}:{size}",
            )
        )
    if nav:
        builder.row(*nav)

    builder.row(
        InlineKeyboardButton(text="🔍 Filter", callback_data=f"filter:{category_id}"),
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="catalog"),
    )
    return builder.as_markup()
