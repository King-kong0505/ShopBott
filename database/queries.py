import aiosqlite
import json
import logging
from typing import Optional, List
from config import DATABASE_PATH, ITEMS_PER_PAGE

logger = logging.getLogger(__name__)


# ─── USERS ───────────────────────────────────────────────────────────────────

async def get_or_create_user(telegram_id: int, username: str = None, full_name: str = None) -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        user = await cur.fetchone()
        if not user:
            await db.execute(
                "INSERT INTO users (telegram_id, username, full_name) VALUES (?, ?, ?)",
                (telegram_id, username, full_name),
            )
            await db.commit()
            cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            user = await cur.fetchone()
        return dict(user)


async def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def update_user_phone(telegram_id: int, phone: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET phone = ? WHERE telegram_id = ?", (phone, telegram_id))
        await db.commit()


# ─── CATEGORIES ──────────────────────────────────────────────────────────────

async def get_all_categories() -> List[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY id")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_category_by_id(category_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def add_category(name: str, emoji: str = "🛍") -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "INSERT INTO categories (name, emoji) VALUES (?, ?)", (name, emoji)
        )
        await db.commit()
        return cur.lastrowid


async def delete_category(category_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE categories SET is_active = 0 WHERE id = ?", (category_id,))
        await db.commit()


# ─── PRODUCTS ────────────────────────────────────────────────────────────────

def _parse_product(row: dict) -> dict:
    p = dict(row)
    p["sizes"] = json.loads(p["sizes"]) if p.get("sizes") else []
    p["colors"] = json.loads(p["colors"]) if p.get("colors") else []
    return p


async def get_products_by_category(
    category_id: int,
    page: int = 1,
    min_price: float = None,
    max_price: float = None,
    color: str = None,
    size: str = None,
) -> tuple:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        conditions = ["category_id = ?", "is_active = 1"]
        params: list = [category_id]

        if min_price is not None and min_price > 0:
            conditions.append("price >= ?")
            params.append(min_price)
        if max_price is not None and max_price > 0:
            conditions.append("price <= ?")
            params.append(max_price)
        if color:
            conditions.append("colors LIKE ?")
            params.append(f"%{color}%")
        if size:
            conditions.append("sizes LIKE ?")
            params.append(f"%{size}%")

        where = " AND ".join(conditions)
        cur = await db.execute(f"SELECT COUNT(*) FROM products WHERE {where}", params)
        total = (await cur.fetchone())[0]

        offset = (page - 1) * ITEMS_PER_PAGE
        cur = await db.execute(
            f"SELECT * FROM products WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [ITEMS_PER_PAGE, offset],
        )
        rows = await cur.fetchall()
        return [_parse_product(r) for r in rows], total


async def get_product_by_id(product_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = await cur.fetchone()
        return _parse_product(row) if row else None


async def get_all_products_admin(page: int = 1) -> tuple:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
        total = (await cur.fetchone())[0]
        offset = (page - 1) * ITEMS_PER_PAGE
        cur = await db.execute(
            """SELECT p.*, c.name as category_name FROM products p
               JOIN categories c ON p.category_id = c.id
               WHERE p.is_active = 1 ORDER BY p.id DESC LIMIT ? OFFSET ?""",
            (ITEMS_PER_PAGE, offset),
        )
        rows = await cur.fetchall()
        return [_parse_product(r) for r in rows], total


async def add_product(
    category_id: int, name: str, description: str, price: float,
    sizes: list, colors: list, image_url: str, stock: int
) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            """INSERT INTO products
               (category_id, name, description, price, sizes, colors, image_url, stock)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (category_id, name, description, price,
             json.dumps(sizes), json.dumps(colors), image_url, stock),
        )
        await db.commit()
        return cur.lastrowid


async def update_product_field(product_id: int, field: str, value):
    allowed = {"name", "description", "price", "image_url", "stock", "sizes", "colors", "category_id"}
    if field not in allowed:
        raise ValueError(f"Field '{field}' not allowed")
    if field in ("sizes", "colors") and isinstance(value, list):
        value = json.dumps(value)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(f"UPDATE products SET {field} = ? WHERE id = ?", (value, product_id))
        await db.commit()


async def update_product_stock(product_id: int, stock: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE products SET stock = ? WHERE id = ?", (stock, product_id))
        await db.commit()


async def delete_product(product_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
        await db.commit()


async def get_all_colors_for_category(category_id: int) -> List[str]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "SELECT colors FROM products WHERE category_id = ? AND is_active = 1", (category_id,)
        )
        rows = await cur.fetchall()
    all_colors = set()
    for (colors_json,) in rows:
        try:
            for c in json.loads(colors_json):
                all_colors.add(c)
        except Exception:
            pass
    return sorted(all_colors)


async def get_all_sizes_for_category(category_id: int) -> List[str]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "SELECT sizes FROM products WHERE category_id = ? AND is_active = 1", (category_id,)
        )
        rows = await cur.fetchall()
    all_sizes = set()
    for (sizes_json,) in rows:
        try:
            for s in json.loads(sizes_json):
                all_sizes.add(s)
        except Exception:
            pass
    return sorted(all_sizes)


# ─── CART ────────────────────────────────────────────────────────────────────

async def get_cart(user_id: int) -> List[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT c.id, c.quantity, c.size, c.color,
                      p.id as product_id, p.name, p.price, p.image_url, p.stock
               FROM cart c JOIN products p ON c.product_id = p.id
               WHERE c.user_id = ?""",
            (user_id,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def add_to_cart(user_id: int, product_id: int, quantity: int, size: str, color: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM cart WHERE user_id=? AND product_id=? AND size=? AND color=?",
            (user_id, product_id, size, color),
        )
        existing = await cur.fetchone()
        if existing:
            await db.execute(
                "UPDATE cart SET quantity = quantity + ? WHERE id = ?", (quantity, existing[0])
            )
        else:
            await db.execute(
                "INSERT INTO cart (user_id, product_id, quantity, size, color) VALUES (?,?,?,?,?)",
                (user_id, product_id, quantity, size, color),
            )
        await db.commit()


async def remove_from_cart(cart_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
        await db.commit()


async def clear_cart(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_cart_total(user_id: int) -> float:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "SELECT SUM(c.quantity * p.price) FROM cart c JOIN products p ON c.product_id=p.id WHERE c.user_id=?",
            (user_id,),
        )
        result = await cur.fetchone()
        return result[0] or 0.0


# ─── ORDERS ──────────────────────────────────────────────────────────────────

async def create_order(
    user_id: int, total_amount: float,
    customer_name: str, phone: str, address: str, notes: str = None
) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            """INSERT INTO orders (user_id, total_amount, customer_name, phone, address, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, total_amount, customer_name, phone, address, notes),
        )
        order_id = cur.lastrowid
        await db.commit()
        return order_id


async def add_order_items(order_id: int, items: List[dict]):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for item in items:
            await db.execute(
                """INSERT INTO order_items
                   (order_id, product_id, product_name, quantity, size, color, price)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (order_id, item["product_id"], item["name"],
                 item["quantity"], item.get("size"), item.get("color"), item["price"]),
            )
            await db.execute(
                "UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?",
                (item["quantity"], item["product_id"]),
            )
        await db.commit()


async def get_user_orders(user_id: int) -> List[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_all_orders(page: int = 1) -> tuple:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT COUNT(*) FROM orders")
        total = (await cur.fetchone())[0]
        offset = (page - 1) * ITEMS_PER_PAGE
        cur = await db.execute(
            """SELECT o.*, u.full_name, u.username FROM orders o
               JOIN users u ON o.user_id = u.id
               ORDER BY o.created_at DESC LIMIT ? OFFSET ?""",
            (ITEMS_PER_PAGE, offset),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows], total


async def get_order_by_id(order_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_order_items(order_id: int) -> List[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()


async def check_user_purchased_product(user_id: int, product_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            """SELECT COUNT(*) FROM order_items oi
               JOIN orders o ON oi.order_id = o.id
               WHERE o.user_id = ? AND oi.product_id = ? AND o.status != 'cancelled'""",
            (user_id, product_id),
        )
        return (await cur.fetchone())[0] > 0


async def get_purchasable_products_for_feedback(user_id: int) -> List[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT DISTINCT p.id, p.name, o.id as order_id
               FROM order_items oi
               JOIN orders o ON oi.order_id = o.id
               JOIN products p ON oi.product_id = p.id
               WHERE o.user_id = ? AND o.status != 'cancelled'
               AND NOT EXISTS (
                   SELECT 1 FROM feedback f
                   WHERE f.user_id = ? AND f.product_id = p.id AND f.order_id = o.id
               )""",
            (user_id, user_id),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ─── FEEDBACK ────────────────────────────────────────────────────────────────

async def add_feedback(
    user_id: int, product_id: int, order_id: int,
    text: str, rating: int, image_file_id: str = None
) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            """INSERT INTO feedback (user_id, product_id, order_id, text, rating, image_file_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, product_id, order_id, text, rating, image_file_id),
        )
        await db.commit()
        return cur.lastrowid


async def get_product_feedback(product_id: int) -> List[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT f.*, u.full_name, u.username FROM feedback f
               JOIN users u ON f.user_id = u.id
               WHERE f.product_id = ? ORDER BY f.created_at DESC""",
            (product_id,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_all_feedback(page: int = 1) -> tuple:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT COUNT(*) FROM feedback")
        total = (await cur.fetchone())[0]
        offset = (page - 1) * ITEMS_PER_PAGE
        cur = await db.execute(
            """SELECT f.*, u.full_name, p.name as product_name FROM feedback f
               JOIN users u ON f.user_id = u.id
               JOIN products p ON f.product_id = p.id
               ORDER BY f.created_at DESC LIMIT ? OFFSET ?""",
            (ITEMS_PER_PAGE, offset),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows], total


# ─── STATS ───────────────────────────────────────────────────────────────────

async def get_admin_stats() -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        orders = (await (await db.execute("SELECT COUNT(*) FROM orders")).fetchone())[0]
        revenue_row = await (await db.execute(
            "SELECT SUM(total_amount) FROM orders WHERE status != 'cancelled'"
        )).fetchone()
        revenue = revenue_row[0] or 0
        products = (await (await db.execute(
            "SELECT COUNT(*) FROM products WHERE is_active = 1"
        )).fetchone())[0]
        pending = (await (await db.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'pending'"
        )).fetchone())[0]
        return {
            "users": users,
            "orders": orders,
            "revenue": revenue,
            "products": products,
            "pending": pending,
        }
