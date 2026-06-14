import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

games = {}
BASE_MULTIPLIER = 1.25


def create_field(mines):
    field = ["safe"] * 25
    for pos in random.sample(range(25), mines):
        field[pos] = "mine"
    return field


def build_board(uid):
    game = games[uid]
    kb = InlineKeyboardMarkup(row_width=5)

    for i in range(25):
        if i in game["opened"]:
            if game["field"][i] == "mine":
                text = "💣"
            else:
                text = "⭐"
        else:
            text = "⬛"

        kb.insert(
            InlineKeyboardButton(
                text=text,
                callback_data=f"mine:{uid}:{i}"
            )
        )

    kb.row(
        InlineKeyboardButton(
            "💰 Забрать",
            callback_data=f"cash:{uid}"
        )
    )

    return kb


def register_handlers(bot, get_user, save_data):

    @bot.message_handler(commands=["mine"])
    def start_game(message):
        uid = str(message.from_user.id)
        args = message.text.split()

        if len(args) != 3:
            return bot.reply_to(message, "Пример:\n/mine 100 3")

        try:
            bet = int(args[1])
            mines = int(args[2])
        except:
            return bot.reply_to(message, "Пиши числа")

        if mines < 1 or mines > 10:
            return bot.reply_to(message, "Мин должно быть от 1 до 10")

        user = get_user(uid)

        if user["stars"] < bet:
            return bot.reply_to(message, "Недостаточно Stars")

        user["stars"] -= bet
        save_data()

        games[uid] = {
            "bet": bet,
            "mines": mines,
            "field": create_field(mines),
            "opened": [],
            "multiplier": 1.0
        }

        bot.send_message(
            message.chat.id,
            f"🎮 Игра началась\n"
            f"💰 Ставка: {bet} 🌠\n"
            f"💣 Мин: {mines}\n"
            f"📈 x1.00",
            reply_markup=build_board(uid)
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("mine:"))
    def mine_click(call):
        bot.answer_callback_query(call.id)

        parts = call.data.split(":")
        uid = parts[1]
        cell = int(parts[2])

        if str(call.from_user.id) != uid:
            return bot.answer_callback_query(call.id, "Это не твоя игра")

        if uid not in games:
            return

        game = games[uid]

        if cell in game["opened"]:
            return

        game["opened"].append(cell)

        if game["field"][cell] == "mine":
            for i in range(25):
                if game["field"][i] == "mine":
                    game["opened"].append(i)

            bot.edit_message_text(
                "💣 Ты проиграл",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=build_board(uid)
            )

            del games[uid]
            return

        game["multiplier"] *= BASE_MULTIPLIER

        bot.edit_message_text(
            f"⭐ Безопасно\n"
            f"💰 Ставка: {game['bet']} 🌠\n"
            f"📈 x{round(game['multiplier'], 2)}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=build_board(uid)
        )

    @bot.callback_query_handler(func=lambda call: not call.data.startswith("mine:", "cash:"))
    def cashout(call):
        bot.answer_callback_query(call.id)

        uid = call.data.split(":")[1]

        if str(call.from_user.id) != uid:
            return

        if uid not in games:
            return

        game = games[uid]
        user = get_user(uid)

        win = int(game["bet"] * game["multiplier"])
        user["stars"] += win

        save_data()

        bot.edit_message_text(
            f"💰 Ты забрал {win} 🌠",
            call.message.chat.id,
            call.message.message_id
        )

        del games[uid]
