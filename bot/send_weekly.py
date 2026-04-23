"""
send_weekly.py — еженедельный разбор, воскресенье 20:00 МСК
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

import bot.utils   as U
import bot.content as C

state  = U.load()
rows   = U.get_week_logs(state)
week   = U.sprint_week(state)
streak = state["current_streak"]
best   = state["best_streak"]

# Обновить стрик по итогам дня (запускается после 23:00)
U.update_streak(state)
U.save(state)
U.git_commit("bot: weekly review " + U.today_str())

U.send(C.weekly_review(rows, week, streak, best))
print(f"[weekly] неделя {week} отправлена")
