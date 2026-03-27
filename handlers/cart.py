import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database import queries as db
from keyboards.cart_kb import get_cart_keyboard, get_checkout_confirm_keyboard, get_order_done_keyboard, get_cancel_keyboard
from states.states import OrderState
from config import ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()


def _fmt_price(price: float) -> str:
    return f"{price:,.0f}".replace(",", " ")


# ─── VIEW CART ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cart")
async def cb_cart(callback: CallbackQuery):
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Avval /start bosing!", show_alert=True)
        return

    items = await db.get_cart(user["id"])
    if not items:
        text = "🛒 <b>Savatcha</b>\n\n❌ Savatcha bo'sh.\n\nKatalogdan mahsulot tanlang!"
    else:
        total = sum(i["price"] * i["quantity"] for i in items)
        lines = ["🛒 <b>Savatcha</b>\n"]
        for item in items:
            lines.append(
                f"• <b>{item['name']}</b>\n"
                f"  📏 {item.get('size', '—')} | 🎨 {item.get('color', '—')} | "
                f"x{item['quantity']} = <b>{_fmt_price(item['price'] * item['quantity'])} so'm</b>"
            )
        lines.append(f"\n💰 <b>Jami: {_fmt_price(total)} so'm</b>")
        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=get_cart_keyboard(items))
    await callback.answer()


@router.callback_query(F.data.startswith("rm_cart:"))
async def cb_remove_from_cart(callback: CallbackQuery):
    cart_id = int(callback.data.split(":")[1])
    await db.remove_from_cart(cart_id)
    await callback.answer("✅ Mahsulot savatchadan o'chirildi!")

    # Refresh cart
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    items = await db.get_cart(user["id"])
    if not items:
        text = "🛒 <b>Savatcha</b>\n\n❌ Savatcha bo'sh."
    else:
        total = sum(i["price"] * i["quantity"] for i in items)
        lines = ["🛒 <b>Savatcha</b>\n"]
        for item in items:
            lines.append(
                f"• <b>{item['name']}</b>\n"
                f"  📏 {item.get('size', '—')} | 🎨 {item.get('color', '—')} | "
                f"x{item['quantity']} = <b>{_fmt_price(item['price'] * item['quantity'])} so'm</b>"
            )
        lines.append(f"\n💰 <b>Jami: {_fmt_price(total)} so'm</b>")
        text = "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=get_cart_keyboard(items))


@router.callback_query(F.data == "clear_cart")
async def cb_clear_cart(callback: CallbackQuery):
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if user:
        await db.clear_cart(user["id"])
    await callback.answer("🗑 Savatcha tozalandi!")
    text = "🛒 <b>Savatcha</b>\n\n❌ Savatcha bo'sh."
    await callback.message.edit_text(text, reply_markup=get_cart_keyboard([]))


# ─── CHECKOUT ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "checkout")
async def cb_checkout(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Avval /start bosing!", show_alert=True)
        return

    items = await db.get_cart(user["id"])
    if not items:
        await callback.answer("❌ Savatcha bo'sh!", show_alert=True)
        return

    await state.set_state(OrderState.waiting_for_name)
    await state.update_data(user_db_id=user["id"])
    await callback.message.edit_text(
        "📋 <b>Buyurtma rasmiylashtirishw</b>\n\n"
        "👤 Ismingiz va familiyangizni kiriting:\n\n"
        "Masalan: <code>Aliyev Sardor</code>",
        reply_markup=get_cancel_keyboard("cart"),
    )
    await callback.answer()


@router.message(OrderState.waiting_for_name)
async def fsm_order_name(message: Message, state: FSMContext):
    await state.update_data(customer_name=message.text.strip())
    await state.set_state(OrderState.waiting_for_phone)
    await message.answer(
        "📱 <b>Telefon raqamingizni kiriting:</b>\n\nMasalan: <code>+998901234567</code>",
        reply_markup=get_cancel_keyboard("cart"),
    )


@router.message(OrderState.waiting_for_phone)
async def fsm_order_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not any(c.isdigit() for c in phone):
        await message.answer("❌ Noto'g'ri telefon raqam. Qaytadan kiriting:")
        return
    await state.update_data(phone=phone)
    await state.set_state(OrderState.waiting_for_address)
    await message.answer(
        "🏠 <b>Yetkazib berish manzilini kiriting:</b>\n\n"
        "Masalan: <code>Toshkent, Chilonzor, 7-mavze, 12-uy</code>",
        reply_markup=get_cancel_keyboard("cart"),
    )


@router.message(OrderState.waiting_for_address)
async def fsm_order_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await state.set_state(OrderState.waiting_for_notes)
    await message.answer(
        "📝 <b>Qo'shimcha izoh (ixtiyoriy):</b>\n\n"
        "Yoki <b>'Yo'q'</b> yozing.",
        reply_markup=get_cancel_keyboard("cart"),
    )


@router.message(OrderState.waiting_for_notes)
async def fsm_order_notes(message: Message, state: FSMContext):
    notes = message.text.strip()
    if notes.lower() in ("yo'q", "yoq", "нет", "no", "-"):
        notes = None
    await state.update_data(notes=notes)
    await state.set_state(OrderState.confirming)

    data = await state.get_data()
    user_db_id = data["user_db_id"]
    items = await db.get_cart(user_db_id)
    total = sum(i["price"] * i["quantity"] for i in items)

    lines = ["📋 <b>Buyurtmani tasdiqlang</b>\n"]
    for item in items:
        lines.append(
            f"• {item['name']} ({item.get('size','—')}/{item.get('color','—')}) "
            f"x{item['quantity']} = {_fmt_price(item['price'] * item['quantity'])} so'm"
        )
    lines.append(f"\n💰 <b>Jami: {_fmt_price(total)} so'm</b>")
    lines.append(f"\n👤 Ism: <b>{data['customer_name']}</b>")
    lines.append(f"📱 Tel: <b>{data['phone']}</b>")
    lines.append(f"🏠 Manzil: <b>{data['address']}</b>")
    if notes:
        lines.append(f"📝 Izoh: <i>{notes}</i>")

    await message.answer("\n".join(lines), reply_markup=get_checkout_confirm_keyboard())


@router.callback_query(F.data == "confirm_order", OrderState.confirming)
async def cb_confirm_order(callback: CallbackQuery, state: FSMContext, bot):
    data = await state.get_data()
    user_db_id = data["user_db_id"]
    items = await db.get_cart(user_db_id)
    if not items:
        await callback.answer("❌ Savatcha bo'sh!", show_alert=True)
        await state.clear()
        return

    total = sum(i["price"] * i["quantity"] for i in items)
    order_id = await db.create_order(
        user_id=user_db_id,
        total_amount=total,
        customer_name=data["customer_name"],
        phone=data["phone"],
        address=data["address"],
        notes=data.get("notes"),
    )

    order_items = [
        {
            "product_id": i["product_id"],
            "name": i["name"],
            "quantity": i["quantity"],
            "size": i.get("size"),
            "color": i.get("color"),
            "price": i["price"],
        }
        for i in items
    ]
    await db.add_order_items(order_id, order_items)
    await db.clear_cart(user_db_id)
    await state.clear()

    # Notify admins
    admin_text = (
        f"🆕 <b>Yangi buyurtma #{order_id}</b>\n\n"
        f"👤 Mijoz: <b>{data['customer_name']}</b>\n"
        f"📱 Tel: <b>{data['phone']}</b>\n"
        f"🏠 Manzil: <b>{data['address']}</b>\n"
        f"💰 Jami: <b>{_fmt_price(total)} so'm</b>\n\n"
        f"Mahsulotlar:\n"
    )
    for item in items:
        admin_text += f"• {item['name']} x{item['quantity']} = {_fmt_price(item['price'] * item['quantity'])} so'm\n"

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception as e:
            logger.error(f"Could not notify admin {admin_id}: {e}")

    success_text = (
        f"✅ <b>Buyurtma #{order_id} muvaffaqiyatli berildi!</b>\n\n"
        f"💰 Jami: <b>{_fmt_price(total)} so'm</b>\n\n"
        f"📦 Tez orada siz bilan bog'lanamiz.\n"
        f"Rahmat xarid qilganingiz uchun! 🙏"
    )
    await callback.message.edit_text(success_text, reply_markup=get_order_done_keyboard())
    await callback.answer()
