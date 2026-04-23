"""
utils.py — общие утилиты: Telegram API, управление состоянием (JSON в репо)
"""
import json
import os
import subprocess
from datetime import date, timedelta
from pathlib import Path

import requests

# ── Пути ─────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent
STATE_FILE = ROOT / "state" / "progress.json"

# ── Telegram ──────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID   = os.environ["CHAT_ID"]
API       = f"https://api.telegram.org/bot{BOT_TOKEN}"

TASKS = ["fa", "ifrs", "excel", "english", "sport"]
TASK_LABELS = {
    "fa":      "Финансовый анализ",
    "ifrs":    "МСФО",
    "excel":   "Excel / Power BI",
    "english": "Английский",
    "sport":   "Спорт",
}


def send(text: str, parse_mode: str = "Markdown") -> dict:
    r = requests.post(f"{API}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text":    text,
        "parse_mode": parse_mode,
    }, timeout=10)
    r.raise_for_status()
    return r.json()


def send_keyboard(text: str, buttons: list) -> dict:
    """Отправить сообщение с Inline-кнопками."""
    r = requests.post(f"{API}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text":    text,
        "parse_mode": "Markdown",
        "reply_markup": {"inline_keyboard": buttons},
    }, timeout=10)
    r.raise_for_status()
    return r.json()


def answer_callback(callback_query_id: str):
    requests.post(f"{API}/answerCallbackQuery",
                  json={"callback_query_id": callback_query_id}, timeout=5)


def edit_message(chat_id, message_id, text: str):
    requests.post(f"{API}/editMessageText", json={
        "chat_id":    chat_id,
        "message_id": message_id,
        "text":       text,
        "parse_mode": "Markdown",
    }, timeout=5)


# ── Состояние (JSON) ──────────────────────────────────────────────────────

def load() -> dict:
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def today_str() -> str:
    return str(date.today())


def ensure_today(state: dict) -> dict:
    """Гарантирует, что запись на сегодня существует в state['logs']."""
    td = today_str()
    if td not in state["logs"]:
        state["logs"][td] = {
            "fa_done":      False,
            "ifrs_done":    False,
            "excel_done":   False,
            "english_done": False,
            "sport_done":   False,
            "total_done":   0,
            "skipped":      [],
        }
    return state


def mark_task(state: dict, task: str) -> bool:
    if task not in TASKS:
        return False
    state = ensure_today(state)
    td    = today_str()
    state["logs"][td][f"{task}_done"] = True
    state["logs"][td]["total_done"]   = sum(
        1 for t in TASKS if state["logs"][td].get(f"{t}_done")
    )
    return True


def skip_task(state: dict, task: str, reason: str = "") -> dict:
    state = ensure_today(state)
    entry = f"{task}:{reason}" if reason else task
    if entry not in state["logs"][today_str()]["skipped"]:
        state["logs"][today_str()]["skipped"].append(entry)
    return state


def update_streak(state: dict):
    """Вызывается в конце дня. Обновляет стрик по итогам дня."""
    td  = today_str()
    log = state["logs"].get(td, {})
    ok  = log.get("total_done", 0) >= 3   # ≥3 из 5 = день засчитан

    if ok:
        state["current_streak"] += 1
        state["total_days"]     += 1
        if state["current_streak"] > state["best_streak"]:
            state["best_streak"] = state["current_streak"]
    else:
        state["current_streak"] = 0


def get_week_logs(state: dict) -> list:
    today = date.today()
    start = today - timedelta(days=today.weekday())
    rows  = []
    for i in range((today - start).days + 1):
        d   = str(start + timedelta(days=i))
        log = state["logs"].get(d, {})
        rows.append({
            "date":      d,
            "fa":        int(log.get("fa_done", False)),
            "ifrs":      int(log.get("ifrs_done", False)),
            "excel":     int(log.get("excel_done", False)),
            "english":   int(log.get("english_done", False)),
            "sport":     int(log.get("sport_done", False)),
            "total":     log.get("total_done", 0),
        })
    return rows


def sprint_day(state: dict) -> int:
    start = date.fromisoformat(state["start_date"])
    return max(1, (date.today() - start).days + 1)


def sprint_week(state: dict) -> int:
    return min(4, max(1, (sprint_day(state) - 1) // 7 + 1))


# ── Git commit (для GitHub Actions) ──────────────────────────────────────

def git_commit(message: str = "bot: update progress"):
    """
    Коммитит state/progress.json обратно в репозиторий.
    Работает внутри GitHub Actions (GITHUB_TOKEN уже настроен).
    """
    try:
        subprocess.run(["git", "config", "user.name",  "FA Bot"], check=True)
        subprocess.run(["git", "config", "user.email", "bot@fa-sprint.local"], check=True)
        subprocess.run(["git", "add",    str(STATE_FILE)], check=True)
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], capture_output=True
        )
        if result.returncode != 0:   # есть изменения
            subprocess.run(["git", "commit", "-m", message], check=True)
            subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[git] ошибка: {e}")
