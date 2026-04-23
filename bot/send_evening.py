"""
send_evening.py — вечерний чек-ин 21:00 МСК
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

import bot.utils   as U
import bot.content as C

state = U.load()
name  = state["name"]

buttons = [
    [
        {"text": "✅ Фин. анализ", "callback_data": "done_fa"},
        {"text": "✅ МСФО",        "callback_data": "done_ifrs"},
    ],
    [
        {"text": "✅ Excel",        "callback_data": "done_excel"},
        {"text": "✅ Английский",   "callback_data": "done_english"},
    ],
    [
        {"text": "✅ Спорт",        "callback_data": "done_sport"},
        {"text": "📊 Итог дня",     "callback_data": "status"},
    ],
]

U.send_keyboard(C.evening_checkin(name), buttons)
print("[evening] check-in sent")
