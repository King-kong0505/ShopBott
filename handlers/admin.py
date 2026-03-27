import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import queries as db
from keyboards.admin_kb import (
    get_admin_menu,
    get_admin_products_menu,
    get_admin_categories_menu,
    get_admin_product_list,
    get_admin_category_list,
    get_admin_edit_fields_keyboard,
    get_admin_order_status_keyboard,
    get_admin_orders_list,
    get_admin_feedback_list,
)
from states.states import (
    AdminAddProductState,
    AdminEditProductState,
    AdminAddCategoryState,
    AdminManageStockState,
)
from config import ADMIN_IDS, ITEMS_PER_PAGE

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _fmt_price(price: float) -> str:
    return f"{price:,.0f}".replace(",", " ")


# ─── ADMIN ENTRY ─────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqlari yo'q.")
        return
    await message.answer("👑 <b>Admin panel</b>", reply_markup=get_admin_menu())


@router.callback_query(F.data == "admin_menu")
async def cb_admin_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text("👑 <b>Admin panel</b>", reply_markup=get_admin_menu())
    await callback.answer()


# ─── STATS ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    stats = await db.get_admin_stats()
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{stats['users']}</b>\n"
        f"📦 Mahsulotlar: <b>{stats['products']}</b>\n"
        f"📋 Jami buyurtmalar: <b>{stats['orders']}</b>\n"
        f"🕐 Kutilayotganlar: <b>{stats['pending']}</b>\n"
        f"💰 Jami daromad: <b>{_fmt_price(stats['revenue'])} so'm</b>"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Admin menyu", callback_data="admin_menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


# ─── PRODUCTS ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_products")
async def cb_admin_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await callback.message.edit_text("📦 <b>Mahsulotlar boshqaruvi</b>", reply_markup=get_admin_products_menu())
    await callback.answer()


# ADD PRODUCT ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_add_product")
async def cb_admin_add_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    categories = await db.get_all_categories()
    kb = get_admin_category_list(categories, "addprod_cat")
    await callback.message.edit_text(
        "➕ <b>Yangi mahsulot qo'shish</b>\n\nKategoriyani tanlang:",
        reply_markup=kb,
    )
    await state.set_state(AdminAddProductState.choosing_category)
    await callback.answer()


@router.callback_query(F.data.startswith("addprod_cat:"), AdminAddProductState.choosing_category)
async def fsm_addprod_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=category_id)
    await state.set_state(AdminAddProductState.waiting_for_name)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor", callback_data="admin_products"))
    await callback.message.edit_text("📝 Mahsulot nomini kiriting:", reply_markup=builder.as_markup())
    await callback.answer()


@router.message(AdminAddProductState.waiting_for_name)
async def fsm_addprod_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminAddProductState.waiting_for_description)
    await message.answer("📄 Mahsulot tavsifini kiriting:")


@router.message(AdminAddProductState.waiting_for_description)
async def fsm_addprod_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminAddProductState.waiting_for_price)
    await message.answer("💰 Narxni kiriting (so'm):\nMasalan: <code>150000</code>")


@router.message(AdminAddProductState.waiting_for_price)
async def fsm_addprod_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(" ", "").replace(",", ""))
        await state.update_data(price=price)
        await state.set_state(AdminAddProductState.waiting_for_sizes)
        await message.answer(
            "📏 O'lchamlarni kiriting (vergul bilan ajrating):\n"
            "Masalan: <code>S, M, L, XL</code>\n\nYoki <code>-</code> kiriting."
        )
    except ValueError:
        await message.answer("❌ Noto'g'ri narx. Qaytadan kiriting:")


@router.message(AdminAddProductState.waiting_for_sizes)
async def fsm_addprod_sizes(message: Message, state: FSMContext):
    text = message.text.strip()
    sizes = [] if text == "-" else [s.strip() for s in text.split(",") if s.strip()]
    await state.update_data(sizes=sizes)
    await state.set_state(AdminAddProductState.waiting_for_colors)
    await message.answer(
        "🎨 Ranglarni kiriting (vergul bilan):\n"
        "Masalan: <code>Qizil, Ko'k, Oq</code>\n\nYoki <code>-</code>."
    )


@router.message(AdminAddProductState.waiting_for_colors)
async def fsm_addprod_colors(message: Message, state: FSMContext):
    text = message.text.strip()
    colors = [] if text == "-" else [c.strip() for c in text.split(",") if c.strip()]
    await state.update_data(colors=colors)
    await state.set_state(AdminAddProductState.waiting_for_image)
    await message.answer(
        "🖼 Rasm URL manzilini kiriting:\n"
        "Masalan: <code>https://example.com/image.jpg</code>\n\nYoki <code>-</code>."
    )


@router.message(AdminAddProductState.waiting_for_image)
async def fsm_addprod_image(message: Message, state: FSMContext):
    url = message.text.strip()
    await state.update_data(image_url=url if url != "-" else None)
    await state.set_state(AdminAddProductState.waiting_for_stock)
    await message.answer("📦 Stok miqdorini kiriting:\nMasalan: <code>50</code>")


@router.message(AdminAddProductState.waiting_for_stock)
async def fsm_addprod_stock(message: Message, state: FSMContext):
    try:
        stock = int(message.text.strip())
        data = await state.get_data()
        product_id = await db.add_product(
            category_id=data["category_id"],
            name=data["name"],
            description=data["description"],
            price=data["price"],
            sizes=data["sizes"],
            colors=data["colors"],
            image_url=data.get("image_url"),
            stock=stock,
        )
        await state.clear()
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin_products"))
        builder.row(InlineKeyboardButton(text="👑 Admin menyu", callback_data="admin_menu"))
        await message.answer(
            f"✅ Mahsulot <b>#{product_id}</b> muvaffaqiyatli qo'shildi!\n\n"
            f"📝 Nomi: <b>{data['name']}</b>\n"
            f"💰 Narx: <b>{_fmt_price(data['price'])} so'm</b>\n"
            f"📦 Stok: <b>{stock}</b>",
            reply_markup=builder.as_markup(),
        )
    except ValueError:
        await message.answer("❌ Noto'g'ri son. Qaytadan kiriting:")


# EDIT PRODUCT ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_edit_product:"))
async def cb_admin_edit_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    page = int(callback.data.split(":")[1])
    products, total = await db.get_all_products_admin(page)
    await state.set_state(AdminEditProductState.choosing_product)
    kb = get_admin_product_list(products, "editprod", page)
    await callback.message.edit_text(
        f"✏️ <b>Mahsulot tahrirlash</b>\nJami: {total}\n\nMahsulotni tanlang:",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("editprod:"), AdminEditProductState.choosing_product)
async def fsm_edit_choose_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi!", show_alert=True)
        return
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminEditProductState.choosing_field)
    text = (
        f"✏️ <b>{product['name']}</b>\n\n"
        f"💰 {_fmt_price(product['price'])} so'm | 📦 Stok: {product['stock']}\n\n"
        "Qaysi maydonni tahrirlash?"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_edit_fields_keyboard(product_id))
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:"), AdminEditProductState.choosing_field)
async def fsm_edit_choose_field(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    product_id = int(parts[1])
    field = parts[2]
    await state.update_data(edit_field=field)
    await state.set_state(AdminEditProductState.waiting_for_value)
    hints = {
        "name": "Yangi nomni kiriting:",
        "description": "Yangi tavsifni kiriting:",
        "price": "Yangi narxni kiriting (so'm):",
        "stock": "Yangi stok miqdorini kiriting:",
        "sizes": "O'lchamlarni kiriting (vergul bilan): S, M, L",
        "colors": "Ranglarni kiriting (vergul bilan): Qizil, Ko'k",
        "image_url": "Yangi rasm URL kiriting:",
    }
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor", callback_data=f"editprod:{product_id}"))
    await callback.message.edit_text(hints.get(field, "Yangi qiymat kiriting:"), reply_markup=builder.as_markup())
    await callback.answer()


@router.message(AdminEditProductState.waiting_for_value)
async def fsm_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data["edit_field"]
    product_id = data["edit_product_id"]
    raw = message.text.strip()

    try:
        if field == "price":
            value = float(raw.replace(" ", "").replace(",", ""))
        elif field == "stock":
            value = int(raw)
        elif field in ("sizes", "colors"):
            value = [v.strip() for v in raw.split(",") if v.strip()]
        else:
            value = raw

        await db.update_product_field(product_id, field, value)
        await state.clear()
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin_products"))
        await message.answer(f"✅ <b>{field}</b> muvaffaqiyatli yangilandi!", reply_markup=builder.as_markup())
    except Exception as e:
        await message.answer(f"❌ Xato: {e}\nQaytadan kiriting:")


# DELETE PRODUCT ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_delete_product:"))
async def cb_admin_delete_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    page = int(callback.data.split(":")[1])
    products, _ = await db.get_all_products_admin(page)
    kb = get_admin_product_list(products, "delprod", page)
    await callback.message.edit_text("🗑 <b>O'chirish uchun mahsulot tanlang:</b>", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("delprod:"))
async def cb_admin_delete_product(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(product_id)
    if product:
        await db.delete_product(product_id)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin_products"))
    await callback.message.edit_text(
        f"✅ Mahsulot <b>'{product['name'] if product else ''}'</b> o'chirildi.",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


# MANAGE STOCK ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_manage_stock:"))
async def cb_admin_manage_stock(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    page = int(callback.data.split(":")[1])
    products, _ = await db.get_all_products_admin(page)
    await state.set_state(AdminManageStockState.choosing_product)
    kb = get_admin_product_list(products, "stockprod", page)
    await callback.message.edit_text("📊 <b>Stok boshqarish</b>\n\nMahsulotni tanlang:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("stockprod:"), AdminManageStockState.choosing_product)
async def fsm_stock_choose(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("Topilmadi!", show_alert=True)
        return
    await state.update_data(stock_product_id=product_id, stock_product_name=product["name"])
    await state.set_state(AdminManageStockState.waiting_for_stock)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor", callback_data="admin_products"))
    await callback.message.edit_text(
        f"📊 <b>{product['name']}</b>\nJoriy stok: <b>{product['stock']}</b>\n\nYangi stok kiriting:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.message(AdminManageStockState.waiting_for_stock)
async def fsm_stock_value(message: Message, state: FSMContext):
    try:
        stock = int(message.text.strip())
        data = await state.get_data()
        await db.update_product_stock(data["stock_product_id"], stock)
        await state.clear()
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin_products"))
        await message.answer(
            f"✅ <b>{data['stock_product_name']}</b> stoki <b>{stock}</b> ga yangilandi!",
            reply_markup=builder.as_markup(),
        )
    except ValueError:
        await message.answer("❌ Noto'g'ri. Faqat son kiriting:")


# ─── CATEGORIES ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_categories")
async def cb_admin_categories(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await callback.message.edit_text("📂 <b>Kategoriyalar</b>", reply_markup=get_admin_categories_menu())
    await callback.answer()


@router.callback_query(F.data == "admin_add_category")
async def cb_admin_add_category(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await state.set_state(AdminAddCategoryState.waiting_for_name)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor", callback_data="admin_categories"))
    await callback.message.edit_text(
        "➕ <b>Yangi kategoriya</b>\n\nKategoriya nomini kiriting:\nMasalan: <code>Sport kiyimlari</code>",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.message(AdminAddCategoryState.waiting_for_name)
async def fsm_add_cat_name(message: Message, state: FSMContext):
    await state.update_data(cat_name=message.text.strip())
    await state.set_state(AdminAddCategoryState.waiting_for_emoji)
    await message.answer("Emoji kiriting (masalan: 👟):\nYoki <code>-</code> (🛍 ishlatiladi).")


@router.message(AdminAddCategoryState.waiting_for_emoji)
async def fsm_add_cat_emoji(message: Message, state: FSMContext):
    emoji = message.text.strip()
    if emoji == "-":
        emoji = "🛍"
    data = await state.get_data()
    cat_id = await db.add_category(data["cat_name"], emoji)
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📂 Kategoriyalar", callback_data="admin_categories"))
    await message.answer(
        f"✅ Kategoriya <b>#{cat_id}</b> qo'shildi!\n{emoji} <b>{data['cat_name']}</b>",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "admin_del_category")
async def cb_admin_del_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    categories = await db.get_all_categories()
    kb = get_admin_category_list(categories, "delcat")
    await callback.message.edit_text("🗑 <b>O'chirish uchun kategoriya tanlang:</b>", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("delcat:"))
async def cb_delete_category(callback: CallbackQuery):
    cat_id = int(callback.data.split(":")[1])
    await db.delete_category(cat_id)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📂 Kategoriyalar", callback_data="admin_categories"))
    await callback.message.edit_text("✅ Kategoriya o'chirildi.", reply_markup=builder.as_markup())
    await callback.answer()


# ─── ORDERS ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_orders:"))
async def cb_admin_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    page = int(callback.data.split(":")[1])
    orders, total = await db.get_all_orders(page)
    text = f"📋 <b>Buyurtmalar</b> (jami: {total})"
    kb = get_admin_orders_list(orders, total, page, ITEMS_PER_PAGE)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_detail:"))
async def cb_admin_order_detail(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await db.get_order_by_id(order_id)
    if not order:
        await callback.answer("Topilmadi!", show_alert=True)
        return
    items = await db.get_order_items(order_id)
    lines = [
        f"📋 <b>Buyurtma #{order_id}</b>",
        f"📅 {str(order.get('created_at',''))[:16]}",
        f"📊 Holat: <b>{order['status']}</b>",
        f"👤 {order.get('customer_name','—')}",
        f"📱 {order.get('phone','—')}",
        f"🏠 {order.get('address','—')}",
        "",
    ]
    for item in items:
        lines.append(f"• {item['product_name']} x{item['quantity']} = {_fmt_price(item['price']*item['quantity'])} so'm")
    lines.append(f"\n💰 <b>Jami: {_fmt_price(order['total_amount'])} so'm</b>")
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=get_admin_order_status_keyboard(order_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_status:"))
async def cb_admin_order_status(callback: CallbackQuery):
    parts = callback.data.split(":")
    order_id = int(parts[1])
    status = parts[2]
    await db.update_order_status(order_id, status)
    await callback.answer(f"✅ Holat yangilandi: {status}", show_alert=True)
    # Refresh
    order = await db.get_order_by_id(order_id)
    if order:
        items = await db.get_order_items(order_id)
        lines = [
            f"📋 <b>Buyurtma #{order_id}</b>",
            f"📅 {str(order.get('created_at',''))[:16]}",
            f"📊 Holat: <b>{status}</b>",
            f"👤 {order.get('customer_name','—')}",
            f"📱 {order.get('phone','—')}",
            f"🏠 {order.get('address','—')}",
            "",
        ]
        for item in items:
            lines.append(f"• {item['product_name']} x{item['quantity']} = {_fmt_price(item['price']*item['quantity'])} so'm")
        lines.append(f"\n💰 <b>Jami: {_fmt_price(order['total_amount'])} so'm</b>")
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=get_admin_order_status_keyboard(order_id),
        )


# ─── FEEDBACK ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_feedback:"))
async def cb_admin_feedback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    page = int(callback.data.split(":")[1])
    feedbacks, total = await db.get_all_feedback(page)
    text = f"⭐ <b>Fikrlar</b> (jami: {total})"
    kb = get_admin_feedback_list(feedbacks, total, page, ITEMS_PER_PAGE)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_fb_detail:"))
async def cb_admin_fb_detail(callback: CallbackQuery):
    # Just show feedback details inline
    await callback.answer("Fikr tanlandi!", show_alert=False)
