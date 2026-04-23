"""
send_morning.py — утреннее сообщение 07:00 МСК
Запускается GitHub Actions по cron.
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

import bot.utils   as U
import bot.content as C

state = U.load()
state = U.ensure_today(state)
U.save(state)

day    = U.sprint_day(state)
week   = U.sprint_week(state)
streak = state["current_streak"]
name   = state["name"]

# Кнопки быстрой отметки задач
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
        {"text": "📊 Статус дня",   "callback_data": "status"},
    ],
]

text = C.morning_message(name, day, week, streak)
U.send_keyboard(text, buttons)
U.git_commit("bot: start day " + U.today_str())
print(f"[morning] День {day}, неделя {week}, серия {streak}")
