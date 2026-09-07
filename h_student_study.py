"""
قسم الدراسة: عرض الوحدات -> الدروس -> صفحة الدرس بكل مكوناتها.
"""
from telegram import Update
from telegram.ext import ContextTypes

from db_core import get_session
from db_crud import (
    get_or_create_user, get_published_units, get_unit, get_published_lessons,
    get_lesson, get_unit_progress_percent, get_lesson_status, mark_lesson_complete,
    touch_last_lesson, get_lesson_videos, get_lesson_files, get_lesson_quizzes,
    get_unit_quiz,
)
from kb_student import (
    units_list_kb, unit_lessons_kb, lesson_page_kb, back_home_kb,
)
from utils_helpers import paginate, progress_bar, safe_edit


async def show_study_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        units = get_published_units(session)
        if not units:
            await safe_edit(
                query,
                "📭 لا توجد وحدات منشورة بعد.\nترقّب إضافتها قريباً!",
                reply_markup=back_home_kb(),
            )
            return
        page_items, total_pages = paginate(units, page)
        text = "📚 اختر الوحدة التي تريد دراستها:"
        await safe_edit(query, text, reply_markup=units_list_kb(page_items, page, total_pages))
    finally:
        session.close()


async def study_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = int(update.callback_query.data.split("_")[-1])
    await show_study_menu(update, context, page)


async def show_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")  # unit_{id}_{page}
    unit_id, page = int(parts[1]), int(parts[2])

    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        unit = get_unit(session, unit_id)
        if not unit:
            await safe_edit(query, "⚠️ لم يتم العثور على الوحدة.", reply_markup=back_home_kb("study"))
            return

        lessons = get_published_lessons(session, unit_id)
        status_map = {l.id: get_lesson_status(session, user, l) for l in lessons}
        percent = get_unit_progress_percent(session, user, unit)

        page_items, total_pages = paginate(lessons, page)
        unit_quiz = get_unit_quiz(session, unit_id)

        text = (
            f"📐 {unit.name}\n\n"
            f"{unit.description or ''}\n\n"
            f"📊 التقدم: {progress_bar(percent)}"
        )
        await safe_edit(
            query, text,
            reply_markup=unit_lessons_kb(unit_id, page_items, page, total_pages, status_map, unit_quiz),
        )
    finally:
        session.close()


def _adjacent_lesson_ids(session, lesson):
    lessons = get_published_lessons(session, lesson.unit_id)
    ids = [l.id for l in lessons]
    idx = ids.index(lesson.id) if lesson.id in ids else -1
    prev_id = ids[idx - 1] if idx > 0 else None
    next_id = ids[idx + 1] if 0 <= idx < len(ids) - 1 else None
    return prev_id, next_id


async def show_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE, lesson_id: int | None = None):
    query = update.callback_query
    await query.answer()
    if lesson_id is None:
        lesson_id = int(query.data.split("_")[1])

    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        lesson = get_lesson(session, lesson_id)
        if not lesson:
            await safe_edit(query, "⚠️ لم يتم العثور على الدرس.", reply_markup=back_home_kb("study"))
            return

        touch_last_lesson(session, user, lesson)

        videos = get_lesson_videos(session, lesson_id)
        files = get_lesson_files(session, lesson_id)
        quizzes = get_lesson_quizzes(session, lesson_id)
        quiz = quizzes[0] if quizzes else None
        prev_id, next_id = _adjacent_lesson_ids(session, lesson)

        status = get_lesson_status(session, user, lesson)
        icon = "✅" if status == "completed" else "▶️"

        text = f"📌 {icon} {lesson.name}\n\n{lesson.description or ''}"
        await safe_edit(
            query, text,
            reply_markup=lesson_page_kb(lesson, bool(videos), bool(files), quiz, prev_id, next_id),
        )
    finally:
        session.close()


async def send_lesson_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lesson_id = int(query.data.split("_")[1])
    session = get_session()
    try:
        videos = get_lesson_videos(session, lesson_id)
        if not videos:
            await query.answer("لا يوجد فيديو لهذا الدرس بعد.", show_alert=True)
            return
        for v in videos:
            caption = f"🎥 {v.name}\n{v.description or ''}"
            if v.file_id:
                await context.bot.send_video(query.message.chat_id, v.file_id, caption=caption)
            elif v.url:
                await context.bot.send_message(query.message.chat_id, f"🎥 {v.name}\n{v.url}")
    finally:
        session.close()


async def send_lesson_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lesson_id = int(query.data.split("_")[1])
    session = get_session()
    try:
        lesson = get_lesson(session, lesson_id)
        content = lesson.content_text or "لا يوجد شرح مكتوب لهذا الدرس بعد."
        await context.bot.send_message(query.message.chat_id, f"📖 {lesson.name}\n\n{content}")
    finally:
        session.close()


async def send_lesson_examples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lesson_id = int(query.data.split("_")[1])
    session = get_session()
    try:
        lesson = get_lesson(session, lesson_id)
        content = lesson.examples_text or "لا توجد أمثلة محلولة لهذا الدرس بعد."
        await context.bot.send_message(query.message.chat_id, f"🧮 أمثلة محلولة - {lesson.name}\n\n{content}")
    finally:
        session.close()


async def send_lesson_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lesson_id = int(query.data.split("_")[1])
    session = get_session()
    try:
        lesson = get_lesson(session, lesson_id)
        content = lesson.exercises_text or "لا توجد تمارين لهذا الدرس بعد."
        await context.bot.send_message(query.message.chat_id, f"✏️ تمارين - {lesson.name}\n\n{content}")
    finally:
        session.close()


async def send_lesson_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lesson_id = int(query.data.split("_")[1])
    session = get_session()
    try:
        files = get_lesson_files(session, lesson_id)
        if not files:
            await query.answer("لا يوجد ملف مرفق لهذا الدرس بعد.", show_alert=True)
            return
        for f in files:
            await context.bot.send_document(query.message.chat_id, f.file_id, caption=f"📄 {f.name}")
    finally:
        session.close()


async def complete_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lesson_id = int(query.data.split("_")[1])
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        lesson = get_lesson(session, lesson_id)
        new_achievements = mark_lesson_complete(session, user, lesson)
        await query.answer("✅ تم تسجيل إكمال الدرس! +10 XP")
        if new_achievements:
            names = "، ".join(a.name for a in new_achievements)
            await context.bot.send_message(
                query.message.chat_id, f"🎉 مبروك! فتحت إنجازاً جديداً: {names}"
            )
        # إعادة رسم صفحة الدرس لتحديث الأيقونة
        await show_lesson(update, context, lesson_id=lesson_id)
    finally:
        session.close()


async def continue_last_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        if not user.last_lesson_id:
            await safe_edit(
                query,
                "📭 لم تبدأ أي درس بعد.\nاضغط 📚 ابدأ الدراسة للانطلاق!",
                reply_markup=back_home_kb(),
            )
            return
        await show_lesson(update, context, lesson_id=user.last_lesson_id)
    finally:
        session.close()
