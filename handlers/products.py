import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InputMediaPhoto
from database import queries as db
from keyboards.product_kb import (
    get_product_keyboard,
    get_size_keyboard,
    get_color_keyboard,
    get_confirm_add_keyboard,
    get_feedback_list_keyboard,
)
from config import ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()


def _fmt_price(price: float) -> str:
    return f"{price:,.0f}".replace(",", " ")


def _build_product_text(product: dict) -> str:
    stock_text = "✅ Mavjud" if product["stock"] > 0 else "❌ Stokda yo'q"
    sizes = ", ".join(product.get("sizes", [])) or "—"
    colors = ", ".join(product.get("colors", [])) or "—"
    return (
        f"🛍 <b>{product['name']}</b>\n\n"
        f"📄 {product.get('description', '—')}\n\n"
        f"💰 Narx: <b>{_fmt_price(product['price'])} so'm</b>\n"
        f"📦 Stok: <b>{product['stock']} dona</b> — {stock_text}\n"
        f"📏 O'lchamlar: <b>{sizes}</b>\n"
        f"🎨 Ranglar: <b>{colors}</b>"
    )


@router.callback_query(F.data.startswith("product:"))
async def cb_product_detail(callback: CallbackQuery):
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2]) if len(parts) > 2 else 0

    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi!", show_alert=True)
        return

    text = _build_product_text(product)
    kb = get_product_keyboard(product, category_id)

    if product.get("image_url"):
        try:
            await callback.message.edit_media(
                InputMediaPhoto(media=product["image_url"], caption=text),
                reply_markup=kb,
            )
        except Exception:
            await callback.message.edit_text(text, reply_markup=kb)
    else:
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── SIZE SELECTION ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("choose_size:"))
async def cb_choose_size(callback: CallbackQuery):
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2]) if len(parts) > 2 else 0

    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi!", show_alert=True)
        return

    if not product.get("sizes"):
        # No sizes, go directly to color
        await _show_color_select(callback, product, category_id, "")
        return

    text = f"📏 <b>O'lcham tanlang</b>\n\n🛍 Mahsulot: <b>{product['name']}</b>"
    kb = get_size_keyboard(product, category_id)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("sel_size:"))
async def cb_size_selected(callback: CallbackQuery):
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])
    size = parts[3]

    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi!", show_alert=True)
        return

    if not product.get("colors"):
        # No colors, go to confirm
        await _show_confirm(callback, product, category_id, size, "")
        return

    await _show_color_select(callback, product, category_id, size)


async def _show_color_select(callback: CallbackQuery, product: dict, category_id: int, selected_size: str):
    text = (
        f"🎨 <b>Rang tanlang</b>\n\n"
        f"🛍 Mahsulot: <b>{product['name']}</b>\n"
        f"📏 O'lcham: <b>{selected_size or '—'}</b>"
    )
    kb = get_color_keyboard(product, category_id, selected_size)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("sel_color:"))
async def cb_color_selected(callback: CallbackQuery):
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])
    size = parts[3]
    color = parts[4]

    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi!", show_alert=True)
        return

    await _show_confirm(callback, product, category_id, size, color)


async def _show_confirm(callback: CallbackQuery, product: dict, category_id: int, size: str, color: str):
    price_fmt = _fmt_price(product["price"])
    text = (
        f"✅ <b>Savatchaga qo'shish</b>\n\n"
        f"🛍 <b>{product['name']}</b>\n"
        f"📏 O'lcham: <b>{size or '—'}</b>\n"
        f"🎨 Rang: <b>{color or '—'}</b>\n"
        f"💰 Narx: <b>{price_fmt} so'm</b>\n\n"
        f"Tasdiqlaysizmi?"
    )
    kb = get_confirm_add_keyboard(product["id"], category_id, size, color)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


# ─── ADD TO CART ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("add_cart:"))
async def cb_add_to_cart(callback: CallbackQuery):
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])
    size = parts[3]
    color = parts[4]

    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Avval /start bosing!", show_alert=True)
        return

    product = await db.get_product_by_id(product_id)
    if not product or product["stock"] <= 0:
        await callback.answer("❌ Bu mahsulot stokda yo'q!", show_alert=True)
        return

    await db.add_to_cart(user["id"], product_id, 1, size, color)
    await callback.answer(f"✅ '{product['name']}' savatchaga qo'shildi!", show_alert=True)

    # Return to product page
    text = _build_product_text(product)
    kb = get_product_keyboard(product, category_id)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass


# ─── CONTACT SELLER ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("contact_seller:"))
async def cb_contact_seller(callback: CallbackQuery, bot: Bot):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(product_id)
    user = callback.from_user

    if not product:
        await callback.answer("Mahsulot topilmadi!", show_alert=True)
        return

    # Notify admins
    admin_text = (
        f"📞 <b>Sotuvchi bilan bog'lanish so'rovi</b>\n\n"
        f"👤 Foydalanuvchi: <a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📱 Username: @{user.username or '—'}\n\n"
        f"🛍 Mahsulot: <b>{product['name']}</b>\n"
        f"💰 Narx: <b>{_fmt_price(product['price'])} so'm</b>\n"
        f"📦 Stok: <b>{product['stock']}</b>"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

    await callback.answer(
        "✅ So'rovingiz yuborildi! Sotuvchi tez orada siz bilan bog'lanadi.",
        show_alert=True,
    )


# ─── VIEW FEEDBACK ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("view_feedback:"))
async def cb_view_feedback(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(product_id)
    feedbacks = await db.get_product_feedback(product_id)

    if not feedbacks:
        text = (
            f"⭐ <b>Fikrlar — {product['name'] if product else ''}</b>\n\n"
            "❌ Hali fikrlar yo'q.\n\n"
            "Bu mahsulotni sotib oling va birinchi fikrni qoldiring!"
        )
    else:
        lines = [f"⭐ <b>Fikrlar — {product['name'] if product else ''}</b>\n"]
        for fb in feedbacks[:10]:
            stars = "⭐" * fb.get("rating", 5)
            name = fb.get("full_name") or fb.get("username") or "Foydalanuvchi"
            date = str(fb.get("created_at", ""))[:10]
            lines.append(f"{stars} <b>{name}</b> ({date})\n<i>{fb['text']}</i>\n")
        text = "\n".join(lines)

    # Try to find category_id for back button
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"product:{product_id}:0"))
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except Exception:
        await callback.message.answer(text, reply_markup=builder.as_markup())
    await callback.answer()
