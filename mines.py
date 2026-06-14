import random

games = {}
BASE_MULTIPLIER = 1.25


def create_field(mines):
    field = ["safe"] * 25
    for i in random.sample(range(25), mines):
        field[i] = "mine"
    return field


def show_field(uid):
    game = games[uid]
    text = ""

    for i in range(25):
        if i in game["opened"]:
            if game["field"][i] == "mine":
                text += "💣 "
            else:
                text += "⭐ "
        else:
            text += f"{i+1}️⃣ "

        if (i + 1) % 5 == 0:
            text += "\n"

    return text


def register_handlers(bot, get_user, save_data):

    @bot.message_handler(commands=['mine'])
    def start_game(message):
        uid = str(message.from_user.id)
        args = message.text.split()

        if len(args) != 3:
            return bot.reply_to(message, "/mine 100 3")

        bet = int(args[1])
        mines = int(args[2])

        if mines < 1 or mines > 10:
            return bot.reply_to(message, "Мин от 1 до 10")

        user = get_user(uid)

        if user["stars"] < bet:
            return bot.reply_to(message, "Недостаточно Stars")

        user["stars"] -= bet
        save_data()

        games[uid] = {
            "bet": bet,
            "field": create_field(mines),
            "opened": [],
            "multiplier": 1.0
        }

        bot.send_message(
            message.chat.id,
            f"🎮 Игра началась\n"
            f"💰 Ставка: {bet} 🌠\n"
            f"💣 Мин: {mines}\n"
            f"📈 x1.00\n\n"
            f"{show_field(uid)}\n\n"
            f"/open номер\n"
            f"/take"
        )

    @bot.message_handler(commands=['open'])
    def open_cell(message):
        uid = str(message.from_user.id)

        if uid not in games:
            return bot.reply_to(message, "Нет активной игры")

        args = message.text.split()

        if len(args) != 2:
            return bot.reply_to(message, "/open 7")

        cell = int(args[1]) - 1

        if cell < 0 or cell > 24:
            return

        game = games[uid]

        if cell in game["opened"]:
            return bot.reply_to(message, "Уже открыта")

        game["opened"].append(cell)

        if game["field"][cell] == "mine":
            bot.send_message(
                message.chat.id,
                f"💣 Ты проиграл\n\n{show_field(uid)}"
            )
            del games[uid]
            return

        game["multiplier"] *= BASE_MULTIPLIER

        bot.send_message(
            message.chat.id,
            f"⭐ Безопасно\n"
            f"📈 x{round(game['multiplier'], 2)}\n\n"
            f"{show_field(uid)}"
        )

    @bot.message_handler(commands=['take'])
    def cashout(message):
        uid = str(message.from_user.id)

        if uid not in games:
            return bot.reply_to(message, "Нет игры")

        game = games[uid]
        user = get_user(uid)

        win = int(game["bet"] * game["multiplier"])
        user["stars"] += win

        save_data()

        bot.send_message(
            message.chat.id,
            f"💰 Ты забрал {win} 🌠"
        )

        del games[uid]

    @bot.message_handler(commands=['pay'])
    def transfer(message):
        args = message.text.split()

        if len(args) != 3:
            return bot.reply_to(message, "/pay id сумма")

        sender = str(message.from_user.id)
        target = str(args[1])
        amount = int(args[2])

        user = get_user(sender)

        if user["stars"] < amount:
            return bot.reply_to(message, "Недостаточно Stars")

        target_user = get_user(target)

        user["stars"] -= amount
        target_user["stars"] += amount

        save_data()

        bot.reply_to(message, f"✅ Переведено {amount} 🌠")
