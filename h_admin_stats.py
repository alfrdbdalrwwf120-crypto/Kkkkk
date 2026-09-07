"""
📊 الإحصائيات | 👥 إدارة الطلاب | 🏆 النقاط والإنجازات | ⚙️ إعدادات البوت
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db_core import get_session
from db_crud import get_global_stats, get_leaderboard, get_all_achievements
from utils_decorators import admin_only
from utils_helpers import safe_edit, paginate
from config import ADMIN_IDS, BOT_DISPLAY_NAME


@admin_only
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        s = get_global_stats(session)
        top = get_leaderboard(session, limit=5)
        lines = [
            "📊 الإحصائيات\n",
            f"👥 إجمالي الطلاب: {s['students']}",
            f"🟢 الطلاب النشطون (آخر 7 أيام): {s['active_students']}",
            f"📚 عدد الوحدات: {s['units']}",
            f"📖 عدد الدروس: {s['lessons']}",
            f"🎥 عدد الفيديوهات: {s['videos']}",
            f"📄 عدد الملفات: {s['files']}",
            f"📝 عدد الاختبارات: {s['quizzes']}",
            f"🧮 عدد الأسئلة: {s['questions']}",
            "",
            "🏅 أفضل الطلاب حسب XP:",
        ]
        for i, u in enumerate(top, 1):
            lines.append(f"{i}. {u.full_name} — {u.xp} XP")

        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="admin_home")]])
        await safe_edit(query, "\n".join(lines), reply_markup=kb)
    finally:
        session.close()


@admin_only
async def show_students(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        from db_crud import get_all_students
        students = get_all_students(session)
        if not students:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="admin_home")]])
            await safe_edit(query, "👥 لا يوجد طلاب مسجلون بعد.", reply_markup=kb)
            return
        page_items, total_pages = paginate(students, page, page_size=10)
        lines = ["👥 قائمة الطلاب\n"]
        for u in page_items:
            lines.append(f"• {u.full_name} (@{u.username or '—'}) — {u.xp} XP — 🔥{u.streak_days}")
        nav = []
        if total_pages > 1:
            if page > 0:
                nav.append(InlineKeyboardButton("◀️", callback_data=f"students_page_{page-1}"))
            nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
            if page < total_pages - 1:
                nav.append(InlineKeyboardButton("▶️", callback_data=f"students_page_{page+1}"))
        rows = [nav] if nav else []
        rows.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_home")])
        await safe_edit(query, "\n".join(lines), reply_markup=InlineKeyboardMarkup(rows))
    finally:
        session.close()


async def show_students_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = int(update.callback_query.data.split("_")[-1])
    await show_students(update, context, page)


@admin_only
async def show_achievements_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        achievements = get_all_achievements(session)
        lines = ["🏆 نظام النقاط والإنجازات\n", "قيم XP الحالية:"]
        lines.append("• إكمال درس = +10 XP")
        lines.append("• اختبار = +20 XP")
        lines.append("• إجابة صحيحة = +5 XP")
        lines.append("• تحدي اليوم = +30 XP")
        lines.append("")
        lines.append("الإنجازات المتاحة:")
        for a in achievements:
            lines.append(f"{a.icon} {a.name} — يتطلب {a.requirement_value} XP")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="admin_home")]])
        await safe_edit(query, "\n".join(lines), reply_markup=kb)
    finally:
        session.close()


@admin_only
async def show_bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admins_str = "\n".join(f"• {a}" for a in ADMIN_IDS) or "— لا يوجد —"
    text = (
        "⚙️ إعدادات البوت\n\n"
        f"📛 الاسم: {BOT_DISPLAY_NAME}\n\n"
        f"👨‍💻 معرفات المدراء (Telegram IDs):\n{admins_str}\n\n"
        "لتغيير المدراء أو التوكن، عدّل ملف .env وأعد تشغيل البوت."
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="admin_home")]])
    await safe_edit(query, text, reply_markup=kb)
