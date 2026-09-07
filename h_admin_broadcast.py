"""
📢 إرسال إعلان لجميع الطلاب.
"""
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden, BadRequest
from telegram.ext import ContextTypes

from db_core import get_session
from db_crud import create_announcement, get_all_students, log_admin_action
from utils_decorators import admin_only
from utils_helpers import safe_edit, is_locked, set_lock

AWAITING_BROADCAST = "admin_broadcast"

ANN_TYPES = [
    ("general", "📢 إعلان عام"), ("new_lesson", "🎥 درس جديد"),
    ("new_quiz", "📝 اختبار جديد"), ("new_file", "📄 ملف جديد"), ("alert", "⏰ تنبيه"),
]


@admin_only
async def show_broadcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rows = [[InlineKeyboardButton(label, callback_data=f"bctype_{code}")] for code, label in ANN_TYPES]
    rows.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_home")])
    await safe_edit(query, "📢 اختر نوع الإعلان:", reply_markup=InlineKeyboardMarkup(rows))


@admin_only
async def choose_broadcast_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ann_type = query.data.split("_", 1)[1]
    context.user_data["bc_type"] = ann_type
    context.user_data["awaiting"] = AWAITING_BROADCAST
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_home")]])
    await safe_edit(query, "✍️ اكتب نص الإعلان الذي تريد إرساله لجميع الطلاب:", reply_markup=kb)


async def handle_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting") != AWAITING_BROADCAST:
        return
    context.user_data["bc_content"] = update.message.text
    context.user_data.pop("awaiting", None)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ إرسال الآن", callback_data="bcsend"),
         InlineKeyboardButton("❌ إلغاء", callback_data="admin_home")],
    ])
    await update.message.reply_text(
        f"📋 معاينة الإعلان:\n\n{update.message.text}\n\nهل تريد الإرسال لجميع الطلاب؟",
        reply_markup=kb,
    )


@admin_only
async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if is_locked(context):
        await query.answer("جارٍ الإرسال بالفعل...", show_alert=False)
        return
    set_lock(context, True)
    await query.answer("جارٍ الإرسال...")

    ann_type = context.user_data.get("bc_type", "general")
    content = context.user_data.get("bc_content", "")

    session = get_session()
    try:
        create_announcement(session, ann_type, content, update.effective_user.id)
        log_admin_action(session, update.effective_user.id, "broadcast", content[:100])
        students = get_all_students(session)
    finally:
        session.close()

    sent, failed = 0, 0
    icon = dict(ANN_TYPES).get(ann_type, "📢").split(" ")[0]
    text = f"{icon} إعلان جديد\n\n{content}"
    for student in students:
        try:
            await context.bot.send_message(student.telegram_id, text)
            sent += 1
        except (Forbidden, BadRequest):
            failed += 1
        await asyncio.sleep(0.05)  # لتجنب حدود Telegram Flood

    context.user_data.pop("bc_type", None)
    context.user_data.pop("bc_content", None)
    set_lock(context, False)

    from kb_admin import admin_panel_kb
    await query.message.reply_text(
        f"✅ تم إرسال الإعلان.\nنجح: {sent} | فشل: {failed}",
        reply_markup=admin_panel_kb(),
    )
