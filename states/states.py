from aiogram.fsm.state import State, StatesGroup


class FilterState(StatesGroup):
    waiting_for_min_price = State()
    waiting_for_max_price = State()


class CartAddState(StatesGroup):
    choosing_size = State()
    choosing_color = State()
    confirming = State()


class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_notes = State()
    confirming = State()


class FeedbackState(StatesGroup):
    choosing_product = State()
    waiting_for_rating = State()
    waiting_for_text = State()
    waiting_for_image = State()


class AdminAddProductState(StatesGroup):
    choosing_category = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_sizes = State()
    waiting_for_colors = State()
    waiting_for_image = State()
    waiting_for_stock = State()


class AdminEditProductState(StatesGroup):
    choosing_product = State()
    choosing_field = State()
    waiting_for_value = State()


class AdminAddCategoryState(StatesGroup):
    waiting_for_name = State()
    waiting_for_emoji = State()


class AdminManageStockState(StatesGroup):
    choosing_product = State()
    waiting_for_stock = State()
