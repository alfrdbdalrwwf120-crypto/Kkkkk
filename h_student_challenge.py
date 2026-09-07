"""
🔥 تحدي اليوم
"""
from telegram import Update
from telegram.ext import ContextTypes

from db_core import get_session
from db_crud import (
    get_or_create_user, get_active_daily_challenge, has_answered_challenge,
    answer_daily_challenge,
)
from kb_student import daily_challenge_kb, back_home_kb
from utils_helpers import safe_edit


async def show_daily_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        challenge = get_active_daily_challenge(session)
        if not challenge:
            await safe_edit(
                query, "📭 لا يوجد تحدي متاح اليوم. عد لاحقاً!", reply_markup=back_home_kb()
            )
            return

        if has_answered_challenge(session, user.id, challenge.id):
            await safe_edit(
                query,
                "✅ لقد أجبت على تحدي اليوم بالفعل.\nترقّب تحدياً جديداً غداً!",
                reply_markup=back_home_kb(),
            )
            return

        text = f"🔥 تحدي اليوم\n\n{challenge.question_text}"
        kb = daily_challenge_kb(challenge.id, challenge)
        if challenge.image_file_id:
            await query.message.reply_photo(challenge.image_file_id, caption=text, reply_markup=kb)
        else:
            await safe_edit(query, text, reply_markup=kb)
    finally:
        session.close()


async def answer_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, challenge_id, option = query.data.split("_")
    challenge_id = int(challenge_id)

    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        challenge = get_active_daily_challenge(session)
        if not challenge or challenge.id != challenge_id:
            await query.answer("انتهت صلاحية هذا التحدي.", show_alert=True)
            return
        if has_answered_challenge(session, user.id, challenge_id):
            await query.answer("لقد أجبت على هذا التحدي من قبل.", show_alert=True)
            return

        await query.answer()
        is_correct = answer_daily_challenge(session, user, challenge, option)
        result_icon = "✅ إجابة صحيحة! +30 XP" if is_correct else "❌ إجابة غير صحيحة"
        text = f"{result_icon}\n\n💡 {challenge.explanation or ''}"
        await safe_edit(query, text, reply_markup=back_home_kb())
    finally:
        session.close()
