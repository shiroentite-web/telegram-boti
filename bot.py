import telebot
import json
import os
import sys
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8607595063:AAF8-b3jsc89T42VvLuMfQ34sPQJF0HjrDg"
bot = telebot.TeleBot(TOKEN)

ADMINS = [8042308513,6345235493,8701230812]

DATA_FILE = "data.json"

if os.path.exists(DATA_FILE):
   os.remove(DATA_FILE)

products = {
    "🇧🇩 Бангладеш": {"rub": 100, "stars": 100, "stock": 127, "desc": "+880"},
    "🇨🇴 Колумбия": {"rub": 100, "stars": 100, "stock": 62, "desc": "+57"},
    "🇪🇬 Египет": {"rub": 100, "stars": 100, "stock": 79, "desc": "+20"},
    "🇺🇸 США": {"rub": 100, "stars": 100, "stock": 82, "desc": "+1"},
}

orders = []
order_id = 1
users = {}


# ---------- SAVE / LOAD ----------
def save_data():
    data = {
        "orders": orders,
        "order_id": order_id,
        "users": users,
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_data():
    global orders, order_id, users, products

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

            orders = data.get("orders", [])
            order_id = data.get("order_id", 1)
            users = data.get("users", {})

load_data()


# ---------- USERS ----------
def get_user(uid):
    uid = str(uid)

    if uid not in users:
        users[uid] = {
            "rub": 0,
            "stars": 0,
            "orders": []
        }
        save_data()

    return users[uid]


# ---------- MENUS ----------
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🛍 Товары", "👤 Профиль", "📦 Мои покупки")
    kb.row("⚙️ Админ панель")
    return kb


def back_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🛍 Товары", "👤 Профиль", "📦 Мои покупки")
    kb.row("⚙️ Админ панель")
    return kb


# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🌍 Магазин запущен",
        reply_markup=main_menu()
    )


# ---------- PROFILE ----------
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    uid = str(message.from_user.id)
    u = get_user(uid)

    rub = u.get("rub", 0)
    stars = u.get("stars", 0)

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📦 Мои покупки")
    kb.row("🛍 Товары", "⚙️ Админ панель")


    text = (
               f"👤 Профиль\n"
               f"🆔 ID: {uid}\n\n"
               f"💰 Баланс: {rub}\n"
               f"⭐ Звёзды: {stars}\n\n"
            )

    bot.send_message(message.chat.id, text, reply_markup=back_menu())

@bot.message_handler(func=lambda m: m.text == "📦 Мои покупки")
def my_orders(message):
    uid = str(message.from_user.id)
    user = get_user(uid)

    if not user["orders"]:
        return bot.send_message(
            message.chat.id,
            "📦 У вас пока нет покупок"
        )

    text = "📦 Ваши покупки:\n\n"

    for o in user["orders"]:
        text += (
            f"#{o['id']}\n"
            f"{o['product']}\n"
            f"{o['status']}\n\n"
        )

    bot.send_message(message.chat.id, text)

# ---------- PRODUCTS ----------
@bot.message_handler(func=lambda m: m.text == "🛍 Товары")
def show_products(message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    for p in products:
        kb.add(KeyboardButton(p))

    kb.add(KeyboardButton("🔙 Назад"))

    bot.send_message(
        message.chat.id,
        "📦 Выберите товар:",
        reply_markup=kb
    )


# ---------- BACK ----------
@bot.message_handler(func=lambda m: m.text == "🔙 Назад")
def back(message):
    bot.send_message(
        message.chat.id,
        "🏠 Главное меню",
        reply_markup=main_menu()
    )


# ---------- PRODUCT PAGE ----------
@bot.message_handler(func=lambda m: m.text in products)
def product_page(message):
    name = message.text
    p = products[name]

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("💰 Купить ₽", callback_data=f"buy_rub|{name}"),
        InlineKeyboardButton("⭐ Купить ⭐", callback_data=f"buy_star|{name}")
    )
    kb.add(
        InlineKeyboardButton("💬 Связь", url="https://t.me/Tamiokolla")
    )

    bot.send_message(
        message.chat.id,
        f"📦 {name}\n"
        f"💰: {p['rub']}\n"
        f"⭐: {p['stars']}\n"
        f"📦 Остаток: {p['stock']}\n"
        f"📝 {p['desc']}",
        reply_markup=kb
    )


# ---------- CREATE ORDER ----------
def create_order(uid, user, product, price, method):
    global order_id

    o = {
        "id": order_id,
        "uid": uid,
        "user": f"@{user.username}" if user.username else f"id:{uid}",
        "product": product,
        "price": price,
        "method": method,
        "status": "⏳ ожидание"
    }

    order_id += 1
    orders.append(o)
    users[str(uid)]["orders"].append(o)

    save_data()
    return o


# ---------- CALLBACK ----------
@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    global orders, users, order_id

    uid = call.from_user.id
    data = call.data

    get_user(uid)

    # BUY RUB
    if data.startswith("buy_rub"):
        _, name = data.split("|")
        p = products[name]

        if p["stock"] <= 0:
            return bot.answer_callback_query(call.id, "Нет в наличии")

        o = create_order(uid, call.from_user, name, p["rub"], "₽")

        bot.send_message(
            call.message.chat.id,
            f"⏳ Заказ #{o['id']} создан"
        )

    # BUY STAR
    elif data.startswith("buy_star"):
        _, name = data.split("|")
        p = products[name]

        if p["stock"] <= 0:
            return bot.answer_callback_query(call.id, "Нет в наличии")

        o = create_order(uid, call.from_user, name, p["stars"], " ⭐")

        bot.send_message(
            call.message.chat.id,
            f"⏳ Заказ #{o['id']} создан"
        )

    # ADMIN SECURITY
    elif uid not in ADMINS:
        return bot.answer_callback_query(call.id, "⛔ Нет доступа")

    # ADMIN ORDERS
    elif data == "admin_orders":
        kb = InlineKeyboardMarkup()
        text = "📦 Заказы:\n\n"

        for o in orders[-10:]:
            text += (
                f"#{o['id']} | {o['product']}\n"
                f"👤 {o['user']}\n"
                f"📊 {o['status']}\n\n"
            )

            kb.add(
                InlineKeyboardButton(
                    f"👁 {o['id']}",
                    callback_data=f"view|{o['id']}"
                )
            )

        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    # VIEW
    elif data.startswith("view"):
        _, oid = data.split("|")
        oid = int(oid)

        for o in orders:
            if o["id"] == oid:
                kb = InlineKeyboardMarkup()
                kb.add(
                    InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve|{oid}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"reject|{oid}")
                )

                bot.send_message(
                    call.message.chat.id,
                    f"📦 Заказ #{o['id']}\n"
                    f"👤 {o['user']}\n"
                    f"📦 {o['product']}\n"
                    f"💰 {o['price']} {o['method']}\n"
                    f"📊 {o['status']}",
                    reply_markup=kb
                )

    # APPROVE
    elif data.startswith("approve"):
        _, oid = data.split("|")
        oid = int(oid)

        for o in orders:
            if o["id"] == oid:
                o["status"] = "✅ оплачено"

                if o["product"] in products:
                    products[o["product"]]["stock"] -= 1

                bot.send_message(o["uid"], f"✅ Заказ #{oid} подтверждён")
                save_data()
                break

    # REJECT
    elif data.startswith("reject"):
        _, oid = data.split("|")
        oid = int(oid)

        for o in orders:
            if o["id"] == oid:
                o["status"] = "❌ отклонён"

                bot.send_message(o["uid"], f"❌ Заказ #{oid} отклонён")
                save_data()
                break

    # RESET
    elif data == "reset_all":
        orders.clear()
        users.clear()
        order_id = 1
        save_data()

        bot.send_message(call.message.chat.id, "♻️ Все данные сброшены")

    # RESTART
    elif data == "restart_bot":
        bot.send_message(call.message.chat.id, "🔄 Перезапуск...")
        os.execv(sys.executable, ['python'] + sys.argv)


# ---------- ADMIN PANEL ----------
@bot.message_handler(func=lambda m: m.text == "⚙️ Админ панель")
def admin(message):
    if message.from_user.id not in ADMINS:
        return bot.send_message(message.chat.id, "⛔ Нет доступа")

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📦 Заказы", callback_data="admin_orders"))
    kb.add(InlineKeyboardButton("♻️ Сброс", callback_data="reset_all"))
    kb.add(InlineKeyboardButton("🔄 Рестарт", callback_data="restart_bot"))

    bot.send_message(
        message.chat.id,
        "⚙️ Админ панель",
        reply_markup=kb
    )

@bot.message_handler(commands=['give'])
def give_money(message):
    if message.from_user.id not in ADMINS:
        return

    try:
        _, user_id, amount = message.text.split()

        user = get_user(user_id)
        user["rub"] += int(amount)

        save_data()

        bot.reply_to(message, "✅ Рубли начислены")

    except:
        bot.reply_to(message, "Пример:\n/give 123456789 100")

@bot.message_handler(commands=['givestar'])
def give_star(message):
    if message.from_user.id not in ADMINS:
        return

    try:
        _, user_id, amount = message.text.split()

        user = get_user(user_id)
        user["stars"] += int(amount)

        save_data()

        bot.reply_to(message, "✅ Звёзды начислены")

    except:
        bot.reply_to(message, "Пример:\n/givestar 123456789 100")

# ---------- AUTO RESTART ----------
print("BOT STARTED")

while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=10)
    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
