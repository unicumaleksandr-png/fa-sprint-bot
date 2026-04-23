"""
send_reminder.py — напоминания в течение дня
Принимает аргумент: midmorning | afternoon
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

import bot.utils   as U
import bot.content as C

slot = sys.argv[1] if len(sys.argv) > 1 else "midmorning"

if slot == "midmorning":
    U.send(C.reminder_midmorning())
    print("[reminder] midmorning sent")
elif slot == "afternoon":
    U.send(C.reminder_afternoon())
    print("[reminder] afternoon sent")
else:
    print(f"[reminder] unknown slot: {slot}", file=sys.stderr)
    sys.exit(1)
