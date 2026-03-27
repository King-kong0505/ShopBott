import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from database.queries import get_or_create_user
from keyboards.main_menu import get_main_menu

logger = logging.getLogger(__name__)
router = Router()

WELCOME_TEXT = (
    "👋 <b>ShopBot'ga xush kelibsiz!</b>\n\n"
    "🛍 Bu yerda siz <b>erkaklar, ayollar va bolalar</b> kiyimlarini topishingiz mumkin.\n\n"
    "📦 Buyurtma bering, fikrlaringizni qoldiring!\n\n"
    "Quyidagi menyudan tanlang 👇"
)

HELP_TEXT = (
    "ℹ️ <b>Yordam</b>\n\n"
    "🛍 <b>Katalog</b> — barcha mahsulotlarni ko'ring\n"
    "🛒 <b>Savatcha</b> — tanlangan mahsulotlar\n"
    "📦 <b>Buyurtmalarim</b> — buyurtmalar tarixi\n"
    "⭐ <b>Fikr qoldirish</b> — sotib olingan mahsulotlarga fikr yozing\n\n"
    "❓ Savol yoki muammo bo'lsa, sotuvchi bilan bog'laning."
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(WELCOME_TEXT, reply_markup=get_main_menu())


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=get_main_menu())
    await callback.answer()


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery):
    from keyboards.main_menu import get_back_to_main
    await callback.message.edit_text(HELP_TEXT, reply_markup=get_back_to_main())
    await callback.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()
