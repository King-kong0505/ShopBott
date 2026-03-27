# 🛍 ShopBot — Telegram E-Commerce Bot

Aiogram 3.x yordamida yozilgan to'liq Telegram internet-do'kon boti (Uzbek tilida).

---

## 📋 Xususiyatlar

- 👔 **3 kategoriya**: Erkaklar, Ayollar, Bolalar
- 🔍 **Filtrlash**: Narx, rang va o'lcham bo'yicha
- 🛒 **Savatcha**: Mahsulot qo'shish, o'chirish, tozalash
- 📦 **Buyurtma berish**: To'liq FSM oqimi (ism → telefon → manzil → tasdiqlash)
- ⭐ **Fikrlar**: Faqat sotib olgan foydalanuvchilar fikr qoldira oladi + rasm
- 👑 **Admin panel**: Mahsulot/kategoriya CRUD, stok boshqarish, buyurtma holati
- 🗃 **SQLite ma'lumotlar bazasi**: Barcha ma'lumotlar saqlanadi
- 📄 **Logging**: Fayl va konsolga

---

## 🗂 Loyiha tuzilmasi

```
ShopBot/
├── bot.py                  # Asosiy fayl
├── config.py               # Sozlamalar (.env dan)
├── .env.example            # .env namunasi
├── requirements.txt        # Kutubxonalar
├── shopbot.log             # Log fayli (avtomatik yaratiladi)
├── shopbot.db              # SQLite DB (avtomatik yaratiladi)
│
├── database/
│   ├── db.py               # Jadvallar yaratish + namunaviy ma'lumotlar
│   └── queries.py          # Barcha DB so'rovlari
│
├── states/
│   └── states.py           # FSM holatlari
│
├── keyboards/
│   ├── main_menu.py        # Bosh menyu
│   ├── catalog_kb.py       # Katalog klaviaturasi
│   ├── product_kb.py       # Mahsulot sahifasi klaviaturasi
│   ├── cart_kb.py          # Savatcha klaviaturasi
│   ├── filter_kb.py        # Filter klaviaturasi
│   └── admin_kb.py         # Admin panel klaviaturasi
│
├── handlers/
│   ├── start.py            # /start, bosh menyu, yordam
│   ├── catalog.py          # Katalog, sahifalash, filter
│   ├── products.py         # Mahsulot sahifasi, savatga qo'shish
│   ├── cart.py             # Savatcha, buyurtma berish
│   ├── orders.py           # Buyurtmalar tarixi
│   ├── feedback.py         # Fikr qoldirish
│   └── admin.py            # Admin panel
│
└── models/
    └── __init__.py
```

---

## ⚙️ O'rnatish va ishga tushirish

### 1. Talablar
- Python 3.10+
- Telegram boti tokeni (@BotFather dan)

### 2. Muhit sozlash

```bash
# Loyiha papkasiga o'ting
cd ShopBot

# Virtual muhit yarating
python -m venv venv

# Aktivlashtiring (Windows)
venv\Scripts\activate

# Aktivlashtiring (Linux/Mac)
source venv/bin/activate

# Kutubxonalarni o'rnating
pip install -r requirements.txt
```

### 3. `.env` fayl yarating

`.env.example` faylini nusxa olib `.env` nomini bering:

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
```

`.env` faylini oching va to'ldiring:

```env
BOT_TOKEN=1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_IDS=123456789,987654321
DATABASE_PATH=shopbot.db
```

> **BOT_TOKEN** — @BotFather dan olasiz  
> **ADMIN_IDS** — Admin bo'lishi kerak bo'lgan Telegram ID lari (vergul bilan)  
> Telegram ID ni bilish uchun @userinfobot ga `/start` yuboring

### 4. Botni ishga tushiring

```bash
python bot.py
```

---

## 👑 Admin buyruqlari

Botda `/admin` buyrug'ini yuboring (faqat ADMIN_IDS da ko'rsatilgan foydalanuvchilar).

### Admin panel imkoniyatlari:
| Funksiya | Tavsif |
|---|---|
| 📦 Mahsulotlar | Qo'shish, tahrirlash, o'chirish |
| 📊 Stok | Stok miqdorini yangilash |
| 📂 Kategoriyalar | Yangi kategoriya qo'shish/o'chirish |
| 📋 Buyurtmalar | Barcha buyurtmalarni ko'rish, holat o'zgartirish |
| ⭐ Fikrlar | Barcha foydalanuvchi fikrlarini ko'rish |
| 📊 Statistika | Foydalanuvchilar, buyurtmalar, daromad |

---

## 🗃 Ma'lumotlar bazasi jadvallari

| Jadval | Tavsif |
|---|---|
| `users` | Bot foydalanuvchilari |
| `categories` | Kiyim kategoriyalari |
| `products` | Mahsulotlar (narx, o'lcham, rang, stok) |
| `cart` | Savatcha elementlari |
| `orders` | Buyurtmalar |
| `order_items` | Buyurtma tarkibi |
| `feedback` | Foydalanuvchi fikrlari |

---

## 📌 Muhim eslatmalar

- Bot birinchi ishga tushganda **15 ta namunaviy mahsulot** avtomatik qo'shiladi
- Fikr qoldirish uchun mahsulot **sotib olingan** bo'lishi kerak
- Stok `0` ga teng bo'lsa mahsulot `❌ Stokda yo'q` ko'rinishida chiqadi
- Admin har yangi buyurtmada Telegram orqali xabar oladi

---

## 🐛 Xatoliklar

Muammo bo'lsa `shopbot.log` faylini tekshiring yoki GitHub'da issue oching.
# ShopBott
