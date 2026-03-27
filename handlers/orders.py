import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import queries as db

logger = logging.getLogger(__name__)
router = Router()

STATUS_LABELS = {
    "pending": "🕐 Kutilmoqda",
    "confirmed": "✅ Tasdiqlangan",
    "shipping": "🚚 Yetkazilmoqda",
    "delivered": "✔️ Yetkazildi",
    "cancelled": "❌ Bekor qilindi",
}


def _fmt_price(price: float) -> str:
    return f"{price:,.0f}".replace(",", " ")


@router.callback_query(F.data == "my_orders")
async def cb_my_orders(callback: CallbackQuery):
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Avval /start bosing!", show_alert=True)
        return

    orders = await db.get_user_orders(user["id"])
    if not orders:
        text = (
            "📦 <b>Buyurtmalarim</b>\n\n"
            "❌ Sizda hali buyurtma yo'q.\n\n"
            "Katalogdan mahsulot tanlang va buyurtma bering!"
        )
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🛍 Katalogga o'tish", callback_data="catalog"))
        builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
        return

    lines = ["📦 <b>Buyurtmalarim</b>\n"]
    for order in orders:
        status = STATUS_LABELS.get(order["status"], order["status"])
        date = str(order.get("created_at", ""))[:10]
        lines.append(
            f"🔖 <b>#{order['id']}</b> — {_fmt_price(order['total_amount'])} so'm\n"
            f"   {status} | 📅 {date}"
        )

    builder = InlineKeyboardBuilder()
    for order in orders[:8]:
        builder.row(
            InlineKeyboardButton(
                text=f"#{order['id']} — {STATUS_LABELS.get(order['status'], '?')}",
                callback_data=f"order_detail:{order['id']}",
            )
        )
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))

    await callback.message.edit_text("\n".join(lines), reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("order_detail:"))
async def cb_order_detail(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await db.get_order_by_id(order_id)
    if not order:
        await callback.answer("Buyurtma topilmadi!", show_alert=True)
        return

    items = await db.get_order_items(order_id)
    status = STATUS_LABELS.get(order["status"], order["status"])

    lines = [
        f"📦 <b>Buyurtma #{order_id}</b>\n",
        f"📅 Sana: {str(order.get('created_at', ''))[:16]}",
        f"📊 Holat: <b>{status}</b>",
        f"👤 Ism: {order.get('customer_name', '—')}",
        f"📱 Tel: {order.get('phone', '—')}",
        f"🏠 Manzil: {order.get('address', '—')}",
    ]
    if order.get("notes"):
        lines.append(f"📝 Izoh: {order['notes']}")
    lines.append("\n<b>Mahsulotlar:</b>")
    for item in items:
        size_color = f"({item.get('size','—')}/{item.get('color','—')})"
        lines.append(
            f"• {item['product_name']} {size_color} "
            f"x{item['quantity']} = {_fmt_price(item['price'] * item['quantity'])} so'm"
        )
    lines.append(f"\n💰 <b>Jami: {_fmt_price(order['total_amount'])} so'm</b>")

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Buyurtmalar", callback_data="my_orders"))
    await callback.message.edit_text("\n".join(lines), reply_markup=builder.as_markup())
    await callback.answer()
