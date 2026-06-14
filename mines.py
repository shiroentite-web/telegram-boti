import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

games = {}

BASE_MULTIPLIER = 1.25


def create_field(mines):
    field = ["safe"] * 25

    mine_positions = random.sample(range(25), mines)

    for pos in mine_positions:
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
                text,
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

    @bot.message_handler(commands=['mine'])
    def start_game(message):
        uid = str(message.from_user.id)

        args = message.text.split()

        if len(args) != 3:
            bot.reply_to(message, "Пример:\n/mine 100 3")
            return

        bet = int(args[1])
        mines = int(args[2])

        if mines < 1 or mines > 10:
            bot.reply_to(message, "Мин должно быть от 1 до 10")
            return

        user = get_user(uid)

        if user["stars"] < bet:
            bot.reply_to(message, "Недостаточно Stars")
            return

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
    def open_cell(call):
        bot.answer_callback_query(call.id)

        data = call.data.split(":")
        uid = data[1]
        cell = int(data[2])

        if str(call.from_user.id) != uid:
            bot.answer_callback_query(call.id, "Это не твоя игра")
            return

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

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cash:"))
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
