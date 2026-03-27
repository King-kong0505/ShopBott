import aiosqlite
import json
import logging
from config import DATABASE_PATH

logger = logging.getLogger(__name__)


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                emoji TEXT DEFAULT '🛍',
                is_active BOOLEAN DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                sizes TEXT DEFAULT '[]',
                colors TEXT DEFAULT '[]',
                image_url TEXT,
                stock INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );

            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                size TEXT,
                color TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                customer_name TEXT,
                phone TEXT,
                address TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                size TEXT,
                color TEXT,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                image_file_id TEXT,
                rating INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (order_id) REFERENCES orders(id)
            );
        """)
        await db.commit()

        cursor = await db.execute("SELECT COUNT(*) FROM categories")
        count = (await cursor.fetchone())[0]
        if count == 0:
            await _insert_sample_data(db)
            logger.info("✅ Sample data inserted.")


async def _insert_sample_data(db: aiosqlite.Connection):
    categories = [
        ("Erkaklar (Men)", "👔"),
        ("Ayollar (Women)", "👗"),
        ("Bolalar (Kids)", "👶"),
    ]
    await db.executemany(
        "INSERT INTO categories (name, emoji) VALUES (?, ?)", categories
    )

    products = [
        # Erkaklar
        (1, "Klassik Ko'ylak", "Yuqori sifatli paxta material. Har qanday tadbirga mos.", 150000,
         '["S","M","L","XL","XXL"]', '["Oq","Ko\'k","Qora"]',
         "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=500", 50),
        (1, "Jeans Shim", "Klassik jeans, 100% paxta. Mustahkam tikuv.", 280000,
         '["28","30","32","34","36"]', '["Ko\'k","Qora","Grey"]',
         "https://images.unsplash.com/photo-1542272604-787c3835535d?w=500", 30),
        (1, "Rasmiy Kostyum", "Premium material. To'y va rasmiy tadbirlar uchun.", 850000,
         '["46","48","50","52","54"]', '["Qora","Navy","Kulrang"]',
         "https://images.unsplash.com/photo-1594938298603-c8148c4b5d5a?w=500", 15),
        (1, "Sport Futbolka", "Nafas oladigan material. Sport va kundalik uchun.", 80000,
         '["S","M","L","XL"]', '["Oq","Qora","Qizil","Ko\'k"]',
         "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500", 100),
        (1, "Yengil Jaket", "Bahori jaket. Engil va issiq.", 320000,
         '["S","M","L","XL","XXL"]', '["Qora","Kulrang","Lacak"]',
         "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=500", 25),
        # Ayollar
        (2, "Ayollar Ko'ylagi", "Elegant dizayn. Maxsus tadbirlar uchun.", 220000,
         '["XS","S","M","L","XL"]', '["Qizil","Ko\'k","Yashil","Qora"]',
         "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500", 35),
        (2, "Ayollar Yubkasi", "Engil va zamonaviy. Kundalik kiyim sifatida.", 130000,
         '["XS","S","M","L"]', '["Oq","Qora","Beige","Qizil"]',
         "https://images.unsplash.com/photo-1583496661160-fb5218f79b67?w=500", 60),
        (2, "Ofis Bluzasi", "Professional ko'rinish uchun. Office style.", 110000,
         '["XS","S","M","L","XL"]', '["Oq","Pushti","Ko\'k"]',
         "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=500", 45),
        (2, "Ayollar Paltosi", "Qishki premium palto. Issiq va chiroyli.", 650000,
         '["S","M","L","XL"]', '["Qora","Camel","Ko\'k"]',
         "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=500", 20),
        (2, "Sport Kostyum", "Ayollar uchun sport kostyumi. Qulay material.", 250000,
         '["XS","S","M","L"]', '["Binafsha","Qora","Pushti"]',
         "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=500", 40),
        # Bolalar
        (3, "Bolalar Futbolkasi", "Rang-barang va chidamli. 100% paxta.", 60000,
         '["86","92","98","104","110","116"]', '["Qizil","Ko\'k","Sariq","Yashil"]',
         "https://images.unsplash.com/photo-1519238263530-99bdd11df2ea?w=500", 80),
        (3, "Bolalar Shimi", "Qulay va chidamli. Aktiv bolalar uchun.", 90000,
         '["86","92","98","104","110"]', '["Ko\'k","Qora","Kulrang"]',
         "https://images.unsplash.com/photo-1471286547726-1d88ef8e2faa?w=500", 70),
        (3, "Bayram Ko'ylagi", "Bayram va tadbirlar uchun chiroyli ko'ylak.", 110000,
         '["92","98","104","110","116"]', '["Oq","Pushti","Ko\'k"]',
         "https://images.unsplash.com/photo-1578587018452-892bacefd3f2?w=500", 55),
        (3, "Bolalar Kombinezon", "Kichik bolalar uchun. Yumshoq material.", 95000,
         '["62","68","74","80","86"]', '["Sariq","Ko\'k","Yashil","Pushti"]',
         "https://images.unsplash.com/photo-1622290291468-a28f7a7dc6a8?w=500", 40),
        (3, "Bolalar Sport Kostyumi", "Aktiv bolalar uchun. Nafas oladigan.", 150000,
         '["98","104","110","116","122"]', '["Ko\'k","Qizil","Yashil"]',
         "https://images.unsplash.com/photo-1503944583220-79d8926e5951?w=500", 35),
    ]

    await db.executemany(
        """INSERT INTO products
           (category_id, name, description, price, sizes, colors, image_url, stock)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        products,
    )
    await db.commit()
