"""
نظام الاختبارات: بدء الاختبار، عرض الأسئلة واحداً تلو الآخر، وحساب النتيجة.
حالة الاختبار الجارية تُحفظ في context.user_data لكل مستخدم (لا تتعارض بين الطلاب).
"""
from telegram import Update
from telegram.ext import ContextTypes

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from db_core import get_session
from db_crud import (
    get_or_create_user, get_quiz, get_quiz_questions, save_quiz_attempt, get_lesson,
)
from db_models import Quiz
from kb_student import quiz_question_kb, quiz_result_kb, back_home_kb
from utils_helpers import safe_edit, paginate

QUIZ_TYPE_LABELS = {
    "quick": "⚡ اختبار سريع",
    "lesson": "📖 اختبار درس",
    "unit": "📐 اختبار وحدة",
    "comprehensive": "🧾 اختبار شامل",
}


def _state_key():
    return "active_quiz"


async def show_quizzes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        quizzes = session.query(Quiz).filter_by(is_published=True).all()
        if not quizzes:
            await safe_edit(query, "📭 لا توجد اختبارات منشورة بعد.", reply_markup=back_home_kb())
            return
        page_items, total_pages = paginate(quizzes, page, page_size=6)
        rows = []
        for q in page_items:
            label = QUIZ_TYPE_LABELS.get(q.quiz_type, "📝")
            rows.append([InlineKeyboardButton(f"{label} {q.name}", callback_data=f"quiz_start_{q.id}")])
        nav = []
        if total_pages > 1:
            if page > 0:
                nav.append(InlineKeyboardButton("◀️", callback_data=f"quizpage_{page-1}"))
            nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
            if page < total_pages - 1:
                nav.append(InlineKeyboardButton("▶️", callback_data=f"quizpage_{page+1}"))
        if nav:
            rows.append(nav)
        rows.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="home")])
        await safe_edit(query, "📝 اختر اختباراً:", reply_markup=InlineKeyboardMarkup(rows))
    finally:
        session.close()


async def quizzes_menu_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = int(update.callback_query.data.split("_")[-1])
    await show_quizzes_menu(update, context, page)


async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    quiz_id = int(query.data.split("_")[-1])

    session = get_session()
    try:
        quiz = get_quiz(session, quiz_id)
        if not quiz:
            await safe_edit(query, "⚠️ الاختبار غير موجود.", reply_markup=back_home_kb())
            return
        questions = get_quiz_questions(session, quiz_id)
        if not questions:
            await safe_edit(query, "📭 لا توجد أسئلة في هذا الاختبار بعد.", reply_markup=back_home_kb())
            return

        context.user_data[_state_key()] = {
            "quiz_id": quiz_id,
            "index": 0,
            "answers": {},
        }
        await _send_question(query, context, quiz_id, questions, 0)
    finally:
        session.close()


async def _send_question(query, context, quiz_id, questions, index):
    q = questions[index]
    text = f"❓ سؤال {index + 1} من {len(questions)}\n\n{q.text}"
    kb = quiz_question_kb(quiz_id, index, q)
    if q.image_file_id:
        try:
            await query.message.reply_photo(q.image_file_id, caption=text, reply_markup=kb)
            return
        except Exception:
            pass
    await safe_edit(query, text, reply_markup=kb)


async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, quiz_id, index, option = query.data.split("_")
    quiz_id, index = int(quiz_id), int(index)

    state = context.user_data.get(_state_key())
    if not state or state["quiz_id"] != quiz_id or state["index"] != index:
        # حالة قديمة/مكررة - تجاهل لمنع الأخطاء عند الضغط المزدوج
        return

    session = get_session()
    try:
        questions = get_quiz_questions(session, quiz_id)
        current_q = questions[index]
        state["answers"][current_q.id] = option
        next_index = index + 1

        if next_index < len(questions):
            state["index"] = next_index
            await _send_question(query, context, quiz_id, questions, next_index)
        else:
            await _finish_quiz(query, context, session, quiz_id, questions, state["answers"])
    finally:
        session.close()


async def _finish_quiz(query, context, session, quiz_id, questions, answers):
    user = get_or_create_user(session, query.from_user)
    quiz = get_quiz(session, quiz_id)
    attempt = save_quiz_attempt(session, user, quiz, answers)

    lines = [
        "🎯 النتيجة",
        "",
        f"{attempt.score} / {attempt.total}",
        f"{attempt.percentage}%",
        "✅ ناجح" if attempt.passed else "🔁 يحتاج مزيداً من المراجعة",
        "",
    ]

    review_lessons = set()
    for q in questions:
        selected = answers.get(q.id)
        correct = selected == q.correct_option
        mark = "✅" if correct else "❌"
        lines.append(f"{mark} {q.text[:60]}")
        if not correct:
            lines.append(f"   💡 {q.explanation or 'راجع الدرس المرتبط بهذا السؤال.'}")
            if q.lesson_id:
                lesson = get_lesson(session, q.lesson_id)
                if lesson:
                    review_lessons.add(lesson.name)

    if review_lessons:
        lines.append("")
        lines.append("📚 الدروس التي تحتاج مراجعة:")
        for name in review_lessons:
            lines.append(f"• {name}")

    context.user_data.pop(_state_key(), None)
    text = "\n".join(lines)
    kb = quiz_result_kb(quiz_id)
    try:
        await query.message.reply_text(text, reply_markup=kb)
    except Exception:
        await safe_edit(query, text, reply_markup=kb)
