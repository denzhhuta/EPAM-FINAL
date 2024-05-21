from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

def on_players_online_press() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    b1 = KeyboardButton(text="Пореглянути бронювання 🕐")
    b2 = KeyboardButton(text="Переглянути всі бронювання 🚫")
    kb.add(b1).add(b2)
    return kb

def on_booking_press() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    b1 = KeyboardButton(text="Стіл 1")
    b2 = KeyboardButton(text="Стіл 2")
    b3 = KeyboardButton(text="Стіл 3")
    b4 = KeyboardButton(text="Стіл 4")
    b5 = KeyboardButton(text="Стіл 5")
    b6 = KeyboardButton(text="Стіл 6")
    b7 = KeyboardButton(text="Стіл 7")
    b8 = KeyboardButton(text="Стіл 8")
    b9 = KeyboardButton(text="Стіл 9")
    back_button = KeyboardButton(text="Назад 🔙")
    kb.add(b1).insert(b2).add(b3).insert(b4).add(b5).insert(b6).add(b7).insert(b8).add(b9).insert(back_button)
    return kb