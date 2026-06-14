import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

games = {}

MINE_LIMIT = 10
BASE_MULTIPLIER = 1.25


def create_field(mines):
    field = ["safe"] * 25
    mine_indexes = random.sample(range(25), mines)

    for i in mine_indexes:
        field[i] = "mine"

    return field

if data[0] == "mine_open":
    bot.answer_callback_query(call.id)

elif data[0] == "mine_cashout":
    bot.answer_callback_query(call.id)

def build_board(uid):
    game = games[uid]
    kb = InlineKeyboardMarkup(row_width=5)

    buttons = []

    for i in range(25):
        if i in game["opened"]:
            if game["field"][i] == "mine":
                text = "💣"
            else:
                text = "⭐"
        else:
            text = "⬛"

        buttons.append(
            InlineKeyboardButton(
                text,
                callback_data=f"mine_open|{uid}|{i}"
            )
        )

    for i in range(0, 25, 5):
        kb.row(*buttons[i:i+5])

    kb.row(
        InlineKeyboardButton(
            "💰 Забрать",
            callback_data=f"mine_cashout|{uid}"
        )
    )

    return kb


def register_handlers(bot, get_user, save_data):

    @bot.message_handler(commands=['mine'])
    def start_mine(message):
        uid = str(message.from_user.id)

        args = message.text.split()

        if len(args) != 3:
            return bot.reply_to(
                message,
                "Пример:\n/mine 100 3"
            )

        try:
            bet = int(args[1])
            mines = int(args[2])
        except:
            return bot.reply_to(message, "Введите числа")

        if mines < 1 or mines > MINE_LIMIT:
            return bot.reply_to(message, "Максимум 10 мин")

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

    @bot.callback_query_handler(
    func=lambda call: not call.data.startswith("mine_")
    )
    def cb(call):
        try:
            uid = str(call.from_user.id)
            data = call.data.split("|")

            if uid != data[1]:
                return bot.answer_callback_query(
                    call.id,
                    "Это не твоя игра"
                )

            game = games.get(uid)

            if not game:
                return bot.answer_callback_query(
                    call.id,
                    "Игра уже закончена"
                )

            # Открытие клетки
            if data[0] == "mine_open":
                cell = int(data[2])

                if cell in game["opened"]:
                    return bot.answer_callback_query(
                        call.id,
                        "Уже открыто"
                    )

                game["opened"].append(cell)

                # Если мина
                if game["field"][cell] == "mine":
                    bot.edit_message_reply_markup(
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=build_board(uid)
                    )

                    bot.answer_callback_query(
                        call.id,
                        "💣 Ты проиграл"
                    )

                    del games[uid]
                    return

                # Если безопасно
                game["multiplier"] *= BASE_MULTIPLIER

                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=build_board(uid)
                )

                bot.answer_callback_query(
                    call.id,
                    f"⭐ x{round(game['multiplier'], 2)}"
                )

            # Забрать выигрыш
            elif data[0] == "mine_cashout":
                user = get_user(uid)

                win = int(game["bet"] * game["multiplier"])
                user["stars"] += win

                save_data()

                bot.edit_message_text(
                    f"💰 Забрано {win} 🌠",
                    call.message.chat.id,
                    call.message.message_id
                )

                del games[uid]

        except Exception as e:
            print("MINE ERROR:", e)
