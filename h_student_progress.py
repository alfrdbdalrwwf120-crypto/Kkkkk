"""
📊 تقدمي  و  🏆 إنجازاتي
"""
from telegram import Update
from telegram.ext import ContextTypes

from db_core import get_session
from db_crud import (
    get_or_create_user, get_published_units, get_unit_progress_percent,
    get_user_quiz_attempts_count, get_user_average_score, get_all_achievements,
    get_user_achievement_ids,
)
from kb_student import back_home_kb
from utils_helpers import progress_bar, safe_edit


async def show_my_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        units = get_published_units(session)
        if units:
            overall = int(
                sum(get_unit_progress_percent(session, user, u) for u in units) / len(units)
            )
        else:
            overall = 0

        completed_lessons = sum(1 for _ in user.progress_items if _.status == "completed")
        quizzes_count = get_user_quiz_attempts_count(session, user.id)
        avg_score = get_user_average_score(session, user.id)

        text = (
            "📊 تقدمي\n\n"
            f"📚 نسبة إكمال المنهج: {progress_bar(overall)}\n\n"
            f"🎥 الدروس المكتملة: {completed_lessons}\n"
            f"📝 عدد الاختبارات: {quizzes_count}\n"
            f"🎯 متوسط الدرجات: {avg_score}%\n"
            f"🔥 أيام الدراسة المتتالية: {user.streak_days or 0}\n"
            f"⭐ النقاط: {user.xp} XP\n"
            f"🏅 المستوى: {user.level_code}"
        )
        await safe_edit(query, text, reply_markup=back_home_kb())
    finally:
        session.close()


async def show_my_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        all_ach = get_all_achievements(session)
        earned_ids = get_user_achievement_ids(session, user.id)

        lines = ["🏆 إنجازاتي\n"]
        for ach in all_ach:
            mark = "✅" if ach.id in earned_ids else "🔒"
            lines.append(f"{mark} {ach.name} — {ach.description}")

        lines.append(f"\n⭐ نقاطك الحالية: {user.xp} XP")
        lines.append(f"🏅 مستواك: {user.level_code}")

        await safe_edit(query, "\n".join(lines), reply_markup=back_home_kb())
    finally:
        session.close()
