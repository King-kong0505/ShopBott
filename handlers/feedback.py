import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, PhotoSize
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database import queries as db
from states.states import FeedbackState

logger = logging.getLogger(__name__)
router = Router()

RATING_EMOJIS = {1: "😞", 2: "😐", 3: "😊", 4: "😃", 5: "🤩"}


@router.callback_query(F.data == "feedback_menu")
async def cb_feedback_menu(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Avval /start bosing!", show_alert=True)
        return

    products = await db.get_purchasable_products_for_feedback(user["id"])
    if not products:
        text = (
            "⭐ <b>Fikr qoldirish</b>\n\n"
            "❌ Fikr qoldirish uchun avval mahsulot sotib olishingiz kerak!\n\n"
            "Yoki barcha sotib olingan mahsulotlarga allaqachon fikr qoldirdingiz."
        )
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🛍 Katalog", callback_data="catalog"))
        builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(
            InlineKeyboardButton(
                text=f"🛍 {product['name']}",
                callback_data=f"leave_feedback:{product['id']}:{product['order_id']}",
            )
        )
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))

    await callback.message.edit_text(
        "⭐ <b>Fikr qoldirish</b>\n\nQaysi mahsulot haqida fikr yozmoqchisiz?",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("leave_feedback:"))
async def cb_start_feedback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    product_id = int(parts[1])
    order_id = int(parts[2])

    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi!", show_alert=True)
        return

    await state.set_state(FeedbackState.waiting_for_rating)
    await state.update_data(fb_product_id=product_id, fb_order_id=order_id, fb_product_name=product["name"])

    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(
            text=f"{RATING_EMOJIS[i]} {i}⭐",
            callback_data=f"fb_rating:{i}",
        )
    builder.adjust(5)
    builder.row(InlineKeyboardButton(text="❌ Bekor", callback_data="feedback_menu"))

    await callback.message.edit_text(
        f"⭐ <b>{product['name']}</b> uchun baho bering:\n\n"
        "1⭐ — Juda yomon\n"
        "2⭐ — Yomon\n"
        "3⭐ — O'rtacha\n"
        "4⭐ — Yaxshi\n"
        "5⭐ — Ajoyib!",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fb_rating:"), FeedbackState.waiting_for_rating)
async def cb_feedback_rating(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split(":")[1])
    await state.update_data(fb_rating=rating)
    await state.set_state(FeedbackState.waiting_for_text)

    data = await state.get_data()
    emoji = RATING_EMOJIS.get(rating, "⭐")

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor", callback_data="feedback_menu"))

    await callback.message.edit_text(
        f"✅ Baho: {emoji} <b>{rating}⭐</b>\n\n"
        f"📝 <b>{data['fb_product_name']}</b> haqida fikringizni yozing:\n\n"
        "<i>Kamida 10 ta belgi kiriting</i>",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.message(FeedbackState.waiting_for_text)
async def fsm_feedback_text(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if len(text) < 10:
        await message.answer("❌ Fikr juda qisqa! Kamida 10 ta belgi kiriting:")
        return

    await state.update_data(fb_text=text)
    await state.set_state(FeedbackState.waiting_for_image)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭ Rasimsiz yuborish", callback_data="fb_no_image"))
    builder.row(InlineKeyboardButton(text="❌ Bekor", callback_data="feedback_menu"))

    await message.answer(
        "📸 <b>Rasm qo'shish (ixtiyoriy)</b>\n\n"
        "Mahsulot rasmi yuboring yoki «Rasimsiz yuborish» tugmasini bosing.",
        reply_markup=builder.as_markup(),
    )


@router.message(FeedbackState.waiting_for_image, F.photo)
async def fsm_feedback_image(message: Message, state: FSMContext):
    photo: PhotoSize = message.photo[-1]
    await state.update_data(fb_image_file_id=photo.file_id)
    await _save_feedback(message, state)


@router.callback_query(F.data == "fb_no_image", FeedbackState.waiting_for_image)
async def cb_feedback_no_image(callback: CallbackQuery, state: FSMContext):
    await state.update_data(fb_image_file_id=None)
    await _save_feedback_from_callback(callback, state)


async def _save_feedback(message: Message, state: FSMContext):
    data = await state.get_data()
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Xato! /start bosing.")
        await state.clear()
        return

    await db.add_feedback(
        user_id=user["id"],
        product_id=data["fb_product_id"],
        order_id=data["fb_order_id"],
        text=data["fb_text"],
        rating=data["fb_rating"],
        image_file_id=data.get("fb_image_file_id"),
    )
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))
    await message.answer(
        f"✅ <b>Fikringiz qabul qilindi!</b>\n\n"
        f"🛍 Mahsulot: <b>{data['fb_product_name']}</b>\n"
        f"⭐ Baho: <b>{data['fb_rating']}/5</b>\n\n"
        f"Fikr bildirganingiz uchun rahmat! 🙏",
        reply_markup=builder.as_markup(),
    )


async def _save_feedback_from_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Xato! /start bosing.", show_alert=True)
        await state.clear()
        return

    await db.add_feedback(
        user_id=user["id"],
        product_id=data["fb_product_id"],
        order_id=data["fb_order_id"],
        text=data["fb_text"],
        rating=data["fb_rating"],
        image_file_id=data.get("fb_image_file_id"),
    )
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))
    await callback.message.edit_text(
        f"✅ <b>Fikringiz qabul qilindi!</b>\n\n"
        f"🛍 Mahsulot: <b>{data['fb_product_name']}</b>\n"
        f"⭐ Baho: <b>{data['fb_rating']}/5</b>\n\n"
        f"Fikr bildirganingiz uchun rahmat! 🙏",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()
