import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import queries as db
from keyboards.catalog_kb import get_categories_keyboard, get_products_keyboard
from keyboards.filter_kb import (
    get_filter_menu,
    get_color_filter_keyboard,
    get_size_filter_keyboard,
    get_cancel_filter_keyboard,
)
from states.states import FilterState
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "catalog")
async def cb_catalog(callback: CallbackQuery):
    categories = await db.get_all_categories()
    text = "📂 <b>Kategoriyalar</b>\n\nBir kategoriyani tanlang:"
    await callback.message.edit_text(text, reply_markup=get_categories_keyboard(categories))
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def cb_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    await state.clear()
    await _show_products(callback, category_id, page=1)


@router.callback_query(F.data.startswith("page:"))
async def cb_page(callback: CallbackQuery):
    parts = callback.data.split(":")
    # page:{category_id}:{page}:{min_price}:{max_price}:{color}:{size}
    category_id = int(parts[1])
    page = int(parts[2])
    min_price = float(parts[3]) if len(parts) > 3 and parts[3] else 0
    max_price = float(parts[4]) if len(parts) > 4 and parts[4] else 0
    color = parts[5] if len(parts) > 5 and parts[5] else ""
    size = parts[6] if len(parts) > 6 and parts[6] else ""
    await _show_products(callback, category_id, page, min_price, max_price, color, size)


async def _show_products(
    callback: CallbackQuery,
    category_id: int,
    page: int = 1,
    min_price: float = 0,
    max_price: float = 0,
    color: str = "",
    size: str = "",
):
    category = await db.get_category_by_id(category_id)
    if not category:
        await callback.answer("Kategoriya topilmadi!", show_alert=True)
        return

    products, total = await db.get_products_by_category(
        category_id=category_id,
        page=page,
        min_price=min_price if min_price > 0 else None,
        max_price=max_price if max_price > 0 else None,
        color=color if color else None,
        size=size if size else None,
    )

    filter_info = ""
    if min_price or max_price or color or size:
        parts = []
        if min_price or max_price:
            parts.append(f"💰 {int(min_price):,}–{int(max_price):,} so'm" if max_price else f"💰 {int(min_price):,}+ so'm")
        if color:
            parts.append(f"🎨 {color}")
        if size:
            parts.append(f"📏 {size}")
        filter_info = "\n🔍 <i>Filtr: " + ", ".join(parts) + "</i>"

    text = (
        f"{category['emoji']} <b>{category['name']}</b>{filter_info}\n\n"
        f"Jami: <b>{total}</b> mahsulot\n"
        f"Mahsulotni tanlang 👇"
    )
    if not products:
        text = f"{category['emoji']} <b>{category['name']}</b>\n\n❌ Mahsulot topilmadi."

    kb = get_products_keyboard(products, total, page, category_id, min_price, max_price, color, size)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ─── FILTER ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("filter:"))
async def cb_filter_menu(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    category = await db.get_category_by_id(category_id)
    text = f"🔍 <b>Filter</b> — {category['name'] if category else ''}\n\nFilter turini tanlang:"
    await callback.message.edit_text(text, reply_markup=get_filter_menu(category_id))
    await callback.answer()


@router.callback_query(F.data.startswith("filter_price:"))
async def cb_filter_price_start(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    await state.set_state(FilterState.waiting_for_min_price)
    await state.update_data(filter_category_id=category_id)
    await callback.message.edit_text(
        "💰 <b>Narx filteri</b>\n\nMinimal narxni kiriting (so'm):\n\n"
        "Masalan: <code>50000</code>",
        reply_markup=get_cancel_filter_keyboard(category_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_color:"))
async def cb_filter_color(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    colors = await db.get_all_colors_for_category(category_id)
    if not colors:
        await callback.answer("Bu kategoriyada rang ma'lumoti yo'q!", show_alert=True)
        return
    await callback.message.edit_text(
        "🎨 <b>Rang bo'yicha filter</b>\n\nRangni tanlang:",
        reply_markup=get_color_filter_keyboard(colors, category_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_size:"))
async def cb_filter_size(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    sizes = await db.get_all_sizes_for_category(category_id)
    if not sizes:
        await callback.answer("Bu kategoriyada o'lcham ma'lumoti yo'q!", show_alert=True)
        return
    await callback.message.edit_text(
        "📏 <b>O'lcham bo'yicha filter</b>\n\nO'lchamni tanlang:",
        reply_markup=get_size_filter_keyboard(sizes, category_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_clear:"))
async def cb_filter_clear(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    await state.clear()
    await _show_products(callback, category_id, page=1)


@router.callback_query(F.data.startswith("apply_color:"))
async def cb_apply_color(callback: CallbackQuery):
    parts = callback.data.split(":")
    category_id = int(parts[1])
    color = parts[2]
    await _show_products(callback, category_id, page=1, color=color)


@router.callback_query(F.data.startswith("apply_size:"))
async def cb_apply_size(callback: CallbackQuery):
    parts = callback.data.split(":")
    category_id = int(parts[1])
    size = parts[2]
    await _show_products(callback, category_id, page=1, size=size)


# ─── FSM: price filter input ─────────────────────────────────────────────────

from aiogram.types import Message


@router.message(FilterState.waiting_for_min_price)
async def fsm_min_price(message: Message, state: FSMContext):
    try:
        min_price = float(message.text.replace(" ", "").replace(",", ""))
        data = await state.get_data()
        category_id = data["filter_category_id"]
        await state.set_state(FilterState.waiting_for_max_price)
        await state.update_data(filter_min_price=min_price)
        from keyboards.filter_kb import get_cancel_filter_keyboard
        await message.answer(
            f"✅ Minimal narx: <b>{int(min_price):,} so'm</b>\n\n"
            "Maksimal narxni kiriting (so'm):\n\nMasalan: <code>500000</code>",
            reply_markup=get_cancel_filter_keyboard(category_id),
        )
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting. Masalan: <code>50000</code>")


@router.message(FilterState.waiting_for_max_price)
async def fsm_max_price(message: Message, state: FSMContext):
    try:
        max_price = float(message.text.replace(" ", "").replace(",", ""))
        data = await state.get_data()
        category_id = data["filter_category_id"]
        min_price = data.get("filter_min_price", 0)
        await state.clear()

        # Simulate a callback to show filtered products
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        products, total = await db.get_products_by_category(
            category_id=category_id, page=1,
            min_price=min_price if min_price > 0 else None,
            max_price=max_price if max_price > 0 else None,
        )
        category = await db.get_category_by_id(category_id)
        filter_info = f"\n🔍 <i>Filtr: 💰 {int(min_price):,}–{int(max_price):,} so'm</i>"
        text = (
            f"{category['emoji']} <b>{category['name']}</b>{filter_info}\n\n"
            f"Jami: <b>{total}</b> mahsulot\nMahsulotni tanlang 👇"
        )
        if not products:
            text = f"{category['emoji']} <b>{category['name']}</b>\n\n❌ Mahsulot topilmadi."
        kb = get_products_keyboard(products, total, 1, category_id, min_price, max_price)
        await message.answer(text, reply_markup=kb)
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting. Masalan: <code>500000</code>")
