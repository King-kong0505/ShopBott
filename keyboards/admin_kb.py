from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin_products"),
        InlineKeyboardButton(text="📂 Kategoriyalar", callback_data="admin_categories"),
    )
    builder.row(
        InlineKeyboardButton(text="📋 Buyurtmalar", callback_data="admin_orders:1"),
        InlineKeyboardButton(text="⭐ Fikrlar", callback_data="admin_feedback:1"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"),
    )
    return builder.as_markup()


def get_admin_products_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Mahsulot qo'shish", callback_data="admin_add_product"))
    builder.row(InlineKeyboardButton(text="✏️ Mahsulot tahrirlash", callback_data="admin_edit_product:1"))
    builder.row(InlineKeyboardButton(text="🗑 Mahsulot o'chirish", callback_data="admin_delete_product:1"))
    builder.row(InlineKeyboardButton(text="📊 Stok boshqarish", callback_data="admin_manage_stock:1"))
    builder.row(InlineKeyboardButton(text="🔙 Admin menyu", callback_data="admin_menu"))
    return builder.as_markup()


def get_admin_categories_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data="admin_add_category"))
    builder.row(InlineKeyboardButton(text="🗑 Kategoriya o'chirish", callback_data="admin_del_category"))
    builder.row(InlineKeyboardButton(text="🔙 Admin menyu", callback_data="admin_menu"))
    return builder.as_markup()


def get_admin_product_list(products: list, action: str, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        icon = "❌" if p["stock"] == 0 else "✅"
        builder.row(
            InlineKeyboardButton(
                text=f"{icon} {p['name']} (stok: {p['stock']})",
                callback_data=f"{action}:{p['id']}",
            )
        )
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"admin_prod_page:{action}:{page-1}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_products"))
    return builder.as_markup()


def get_admin_category_list(categories: list, action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"{cat['emoji']} {cat['name']}",
                callback_data=f"{action}:{cat['id']}",
            )
        )
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_categories"))
    return builder.as_markup()


def get_admin_edit_fields_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    fields = [
        ("📝 Nomi", "name"), ("📄 Tavsif", "description"),
        ("💰 Narx", "price"), ("📦 Stok", "stock"),
        ("📏 O'lchamlar", "sizes"), ("🎨 Ranglar", "colors"),
        ("🖼 Rasm URL", "image_url"),
    ]
    for label, field in fields:
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=f"edit_field:{product_id}:{field}",
            )
        )
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_products"))
    return builder.as_markup()


def get_admin_order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    statuses = [
        ("✅ Tasdiqlangan", "confirmed"),
        ("🚚 Yetkazilmoqda", "shipping"),
        ("✔️ Yetkazildi", "delivered"),
        ("❌ Bekor qilindi", "cancelled"),
    ]
    for label, status in statuses:
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=f"order_status:{order_id}:{status}",
            )
        )
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_orders:1"))
    return builder.as_markup()


def get_admin_orders_list(orders: list, total: int, page: int, items_per_page: int) -> InlineKeyboardMarkup:
    import math
    builder = InlineKeyboardBuilder()
    status_icons = {
        "pending": "🕐", "confirmed": "✅",
        "shipping": "🚚", "delivered": "✔️", "cancelled": "❌",
    }
    for order in orders:
        icon = status_icons.get(order["status"], "📋")
        builder.row(
            InlineKeyboardButton(
                text=f"{icon} #{order['id']} — {order['total_amount']:,.0f} so'm",
                callback_data=f"admin_order_detail:{order['id']}",
            )
        )
    total_pages = max(1, math.ceil(total / items_per_page))
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"admin_orders:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"admin_orders:{page+1}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🔙 Admin menyu", callback_data="admin_menu"))
    return builder.as_markup()


def get_admin_feedback_list(feedbacks: list, total: int, page: int, items_per_page: int) -> InlineKeyboardMarkup:
    import math
    builder = InlineKeyboardBuilder()
    for fb in feedbacks:
        stars = "⭐" * fb.get("rating", 5)
        name = fb.get("full_name") or fb.get("username") or "Foydalanuvchi"
        builder.row(
            InlineKeyboardButton(
                text=f"{stars} {name} — {fb['product_name'][:20]}",
                callback_data=f"admin_fb_detail:{fb['id']}",
            )
        )
    total_pages = max(1, math.ceil(total / items_per_page))
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"admin_feedback:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"admin_feedback:{page+1}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🔙 Admin menyu", callback_data="admin_menu"))
    return builder.as_markup()
