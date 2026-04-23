"""
interactive.py — обработчик команд пользователя.
Запускается каждые 30 минут через GitHub Actions.
Слушает сообщения 8 минут, затем завершается.
"""
import asyncio
import sys
import os
import time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

import bot.utils   as U
import bot.content as C

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)

BOT_TOKEN   = os.environ["BOT_TOKEN"]
CHAT_ID     = int(os.environ["CHAT_ID"])
RUN_SECONDS = int(os.getenv("RUN_SECONDS", "480"))   # 8 минут по умолчанию
START_TIME  = time.time()


def task_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Фин. анализ", callback_data="done_fa"),
         InlineKeyboardButton("✅ МСФО",        callback_data="done_ifrs")],
        [InlineKeyboardButton("✅ Excel",        callback_data="done_excel"),
         InlineKeyboardButton("✅ Английский",   callback_data="done_english")],
        [InlineKeyboardButton("✅ Спорт",        callback_data="done_sport"),
         InlineKeyboardButton("📊 Статус дня",   callback_data="status")],
    ])


# ── Команды ───────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    state = U.load()
    await update.message.reply_text(
        f"👋 Привет, {state['name']}!\n\n"
        "Команды:\n"
        "/plan · /done fa · /skip sport · /report · /week · /progress · /motivation\n\n"
        "Задачи: `fa` · `ifrs` · `excel` · `english` · `sport`",
        parse_mode="Markdown",
    )


async def cmd_plan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    state  = U.load()
    day    = U.sprint_day(state)
    week   = U.sprint_week(state)
    streak = state["current_streak"]
    name   = state["name"]
    text   = C.morning_message(name, day, week, streak)
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=task_keyboard())


async def cmd_ready(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    import random
    responses = [
        "🚀 Отлично. Телефон — в другую комнату. Таймер на 2 часа. Поехали.",
        "💪 Принято. Помни: 50 минут работы, 10 минут отдыха без экрана.",
        "✅ Хорошо. Начни с главного блока. Через 2 часа — ближе к цели.",
    ]
    await update.message.reply_text(random.choice(responses))


async def cmd_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Укажи задачу: `/done fa` · `/done ifrs` · `/done excel` · `/done english` · `/done sport`",
            parse_mode="Markdown")
        return
    task  = args[0].lower()
    state = U.load()
    if U.mark_task(state, task):
        U.save(state)
        U.git_commit(f"bot: done {task} {U.today_str()}")
        done  = state["logs"][U.today_str()]["total_done"]
        label = U.TASK_LABELS.get(task, task)
        text  = f"✅ *{label}* — засчитано!\n\nСегодня: *{done}/5*"
        if done == 5:
            text += "\n\n🔥 Идеальный день!"
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"Неизвестная задача `{task}`. Используй: `fa` · `ifrs` · `excel` · `english` · `sport`",
            parse_mode="Markdown")


async def cmd_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    args   = ctx.args
    task   = args[0].lower() if args else ""
    reason = " ".join(args[1:]) if len(args) > 1 else ""
    if not task:
        await update.message.reply_text("Укажи задачу: `/skip sport усталость`",
                                        parse_mode="Markdown")
        return
    state = U.load()
    U.skip_task(state, task, reason)
    U.save(state)
    U.git_commit(f"bot: skip {task} {U.today_str()}")
    resp  = C.procrastination_response(reason) if reason else (
        "Пропуск зафиксирован.\n\nЕсли разово — ок. Если паттерн — напиши, что мешает."
    )
    await update.message.reply_text(resp, parse_mode="Markdown")


async def cmd_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    state = U.load()
    state = U.ensure_today(state)
    log   = state["logs"][U.today_str()]
    await update.message.reply_text(C.day_status(log), parse_mode="Markdown",
                                    reply_markup=task_keyboard())


async def cmd_week(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    state = U.load()
    rows  = U.get_week_logs(state)
    week  = U.sprint_week(state)
    await update.message.reply_text(
        C.weekly_review(rows, week, state["current_streak"], state["best_streak"]),
        parse_mode="Markdown")


async def cmd_progress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    state  = U.load()
    day    = U.sprint_day(state)
    week   = U.sprint_week(state)
    streak = state["current_streak"]
    best   = state["best_streak"]
    total  = state["total_days"]
    bar    = C.progress_bar(day)
    await update.message.reply_text(
        f"📊 *Прогресс спринта*\n\n"
        f"День: *{day}/30* · Неделя: *{week}/4*\n"
        f"{bar}\n\n"
        f"🔥 Серия: *{streak} дн.* · Рекорд: *{best} дн.*\n"
        f"📅 Дней с данными: *{total}*\n\n"
        f"Продолжай. Ты строишь то, что нельзя купить.",
        parse_mode="Markdown")


async def cmd_motivation(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    await update.message.reply_text(C.motivation(), parse_mode="Markdown")


# ── Callback (inline-кнопки) ──────────────────────────────────────────────

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != CHAT_ID:
        return
    await query.answer()
    data  = query.data
    state = U.load()

    if data.startswith("done_"):
        task = data[5:]
        if U.mark_task(state, task):
            U.save(state)
            U.git_commit(f"bot: done {task} {U.today_str()}")
            done  = state["logs"][U.today_str()]["total_done"]
            label = U.TASK_LABELS.get(task, task)
            text  = f"✅ *{label}* засчитан! Сегодня: *{done}/5*"
            if done == 5:
                text += "\n\n🔥 Идеальный день!"
            await query.edit_message_text(text, parse_mode="Markdown",
                                          reply_markup=task_keyboard())
    elif data == "status":
        state = U.ensure_today(state)
        log   = state["logs"][U.today_str()]
        await query.edit_message_text(C.day_status(log), parse_mode="Markdown",
                                      reply_markup=task_keyboard())


# ── Текстовые сообщения ───────────────────────────────────────────────────

async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    text = update.message.text.lower().strip()

    # Отчёт цифрой (0–5)
    if text.isdigit() and 0 <= int(text) <= 5:
        done  = int(text)
        state = U.load()
        state = U.ensure_today(state)
        # Проставляем задачи по количеству (упрощённо)
        state["logs"][U.today_str()]["total_done"] = done
        U.update_streak(state)
        U.save(state)
        U.git_commit(f"bot: report {done} {U.today_str()}")
        await update.message.reply_text(C.report_response(done), parse_mode="Markdown")
        return

    # Прокрастинационные ключевые слова
    kws = ["устал", "лень", "не хочу", "нет мотивации", "не знаю", "не успеваю"]
    if any(kw in text for kw in kws):
        await update.message.reply_text(
            C.procrastination_response(text), parse_mode="Markdown")
        return

    await update.message.reply_text(
        "Используй команды:\n"
        "/plan · /done · /skip · /report · /week · /progress · /motivation",
        parse_mode="Markdown")


# ── Post-init: останавливаем бота по таймеру ─────────────────────────────

async def on_startup(app: Application):
    async def stopper():
        await asyncio.sleep(RUN_SECONDS)
        print(f"[interactive] {RUN_SECONDS}с истекло — останавливаю")
        await app.stop()
        await app.shutdown()

    asyncio.create_task(stopper())


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(on_startup).build()

    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("plan",       cmd_plan))
    app.add_handler(CommandHandler("ready",      cmd_ready))
    app.add_handler(CommandHandler("done",       cmd_done))
    app.add_handler(CommandHandler("skip",       cmd_skip))
    app.add_handler(CommandHandler("report",     cmd_report))
    app.add_handler(CommandHandler("week",       cmd_week))
    app.add_handler(CommandHandler("progress",   cmd_progress))
    app.add_handler(CommandHandler("motivation", cmd_motivation))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    print(f"[interactive] запуск polling на {RUN_SECONDS}с")
    app.run_polling(drop_pending_updates=False, close_loop=False)


if __name__ == "__main__":
    main()
