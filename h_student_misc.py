"""
📢 الإعلانات  |  📖 مكتبتي  |  ⚙️ الإعدادات
تجميع الأقسام الصغيرة في ملف واحد لتفادي كثرة الملفات الصغيرة جداً.
"""
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db_core import get_session
from db_crud import get_or_create_user, get_recent_announcements, get_published_units
from db_models import FileItem
from kb_student import back_home_kb
from utils_helpers import safe_edit

ANN_ICONS = {
    "general": "📢", "new_lesson": "🎥", "new_quiz": "📝", "new_file": "📄", "alert": "⏰",
}


async def show_announcements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        anns = get_recent_announcements(session, limit=10)
        if not anns:
            await safe_edit(query, "📭 لا توجد إعلانات حالياً.", reply_markup=back_home_kb())
            return
        lines = ["📢 آخر الإعلانات\n"]
        for a in anns:
            icon = ANN_ICONS.get(a.ann_type, "📢")
            date_str = a.sent_at.strftime("%Y-%m-%d") if a.sent_at else ""
            lines.append(f"{icon} [{date_str}] {a.content}")
            lines.append("")
        await safe_edit(query, "\n".join(lines), reply_markup=back_home_kb())
    finally:
        session.close()


async def show_library(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        units = get_published_units(session)
        rows = []
        for u in units:
            rows.append([InlineKeyboardButton(f"📂 {u.name}", callback_data=f"lib_unit_{u.id}")])
        rows.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="home")])
        text = "📖 مكتبتي\n\nاختر الوحدة لعرض كل ملفاتها (ملخصات، أوراق عمل، مراجعات...):"
        await safe_edit(query, text, reply_markup=InlineKeyboardMarkup(rows))
    finally:
        session.close()


async def show_library_unit_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    unit_id = int(query.data.split("_")[-1])
    session = get_session()
    try:
        files = (
            session.query(FileItem)
            .filter_by(unit_id=unit_id, is_published=True)
            .all()
        )
        # أيضاً نجمع ملفات دروس هذه الوحدة
        from db_models import Lesson
        lesson_ids = [l.id for l in session.query(Lesson).filter_by(unit_id=unit_id).all()]
        if lesson_ids:
            lesson_files = (
                session.query(FileItem)
                .filter(FileItem.lesson_id.in_(lesson_ids), FileItem.is_published == True)
                .all()
            )
            files = files + lesson_files

        if not files:
            await query.answer("لا توجد ملفات لهذه الوحدة بعد.", show_alert=True)
            return

        for f in files:
            await context.bot.send_document(query.message.chat_id, f.file_id, caption=f"📄 {f.name}")
    finally:
        session.close()


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        status = "🔔 مفعّلة" if user.notifications_enabled else "🔕 متوقفة"
        text = (
            "⚙️ الإعدادات\n\n"
            f"👤 الاسم: {user.full_name}\n"
            f"🆔 معرفك: {user.telegram_id}\n"
            f"📅 تاريخ الانضمام: {user.registered_at.strftime('%Y-%m-%d')}\n"
            f"🔔 الإشعارات: {status}"
        )
        toggle_label = "🔕 إيقاف الإشعارات" if user.notifications_enabled else "🔔 تفعيل الإشعارات"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(toggle_label, callback_data="toggle_notif")],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")],
        ])
        await safe_edit(query, text, reply_markup=kb)
    finally:
        session.close()


async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        user.notifications_enabled = not user.notifications_enabled
        session.commit()
        await query.answer("تم التحديث ✅")
        await show_settings(update, context)
    finally:
        session.close()
