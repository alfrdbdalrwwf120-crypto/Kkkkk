"""
➕ إضافة محتوى (ومنطق التعديل المشترك).
هذا الملف "محرك" واحد يخدم كل أنواع المحتوى بالاعتماد على utils/forms.py،
لذلك إضافة نوع محتوى جديد مستقبلاً لا يتطلب لمس هذا الملف - فقط إضافة
Schema جديد في FORM_SCHEMAS ودالة حفظ واحدة في SAVE_FUNCS.
"""
from telegram import Update
from telegram.ext import ContextTypes

from db_core import get_session
from db_models import Unit, Lesson, Video, FileItem, Quiz, Question, DailyChallenge
from db_crud import log_admin_action
from kb_admin import admin_panel_kb, add_menu_kb, cancel_only_kb
from utils_decorators import admin_only
from utils_helpers import safe_edit, is_locked, set_lock, clear_conversation_state
from utils_forms import (
    start_form, get_current_field, advance_field, store_value, is_form_complete,
    clear_form, build_field_prompt, summarize_form, FORM_TYPE_KEY, FORM_DATA_KEY,
    FORM_EDIT_ID_KEY,
)

AWAITING_FORM = "admin_form"


# ------------------------------------------------------------------ #
# دوال الحفظ لكل نوع محتوى
# ------------------------------------------------------------------ #
def _save_unit(session, data, edit_id):
    obj = session.query(Unit).get(edit_id) if edit_id else Unit()
    obj.name = data["name"]
    obj.description = data.get("description") or ""
    obj.order = int(data["order"])
    obj.image_file_id = data.get("image_file_id")
    obj.is_published = bool(int(data["is_published"]))
    if not edit_id:
        session.add(obj)
    session.commit()
    return obj


def _save_lesson(session, data, edit_id):
    obj = session.query(Lesson).get(edit_id) if edit_id else Lesson()
    obj.unit_id = int(data["unit_id"])
    obj.name = data["name"]
    obj.description = data.get("description") or ""
    obj.content_text = data.get("content_text") or ""
    obj.order = int(data["order"])
    obj.is_published = bool(int(data["is_published"]))
    if not edit_id:
        session.add(obj)
    session.commit()
    return obj


def _save_video(session, data, edit_id):
    obj = session.query(Video).get(edit_id) if edit_id else Video()
    obj.lesson_id = int(data["lesson_id"])
    obj.name = data["name"]
    obj.description = data.get("description") or ""
    video_val = data.get("video") or {}
    obj.file_id = video_val.get("file_id")
    obj.url = video_val.get("url")
    obj.order = int(data["order"])
    obj.is_published = bool(int(data["is_published"]))
    if not edit_id:
        session.add(obj)
    session.commit()
    return obj


def _save_file(session, data, edit_id):
    obj = session.query(FileItem).get(edit_id) if edit_id else FileItem()
    obj.unit_id = int(data["unit_id"]) if data.get("unit_id") else None
    obj.lesson_id = int(data["lesson_id"]) if data.get("lesson_id") else None
    obj.name = data["name"]
    obj.file_id = data["document"]
    obj.description = data.get("description") or ""
    obj.file_type = data.get("file_type", "pdf")
    obj.is_published = bool(int(data["is_published"]))
    if not edit_id:
        session.add(obj)
    session.commit()
    return obj


def _save_quiz(session, data, edit_id):
    obj = session.query(Quiz).get(edit_id) if edit_id else Quiz()
    obj.name = data["name"]
    obj.quiz_type = data["quiz_type"]
    obj.unit_id = int(data["unit_id"]) if data.get("unit_id") else None
    obj.lesson_id = int(data["lesson_id"]) if data.get("lesson_id") else None
    obj.duration_minutes = int(data["duration_minutes"])
    obj.pass_score = int(data["pass_score"])
    obj.is_published = bool(int(data["is_published"]))
    if not edit_id:
        session.add(obj)
    session.commit()
    return obj


def _save_question(session, data, edit_id):
    obj = session.query(Question).get(edit_id) if edit_id else Question()
    obj.quiz_id = int(data["quiz_id"])
    obj.text = data["text"]
    obj.image_file_id = data.get("image_file_id")
    obj.option_a = data["option_a"]
    obj.option_b = data["option_b"]
    obj.option_c = data["option_c"]
    obj.option_d = data["option_d"]
    obj.correct_option = data["correct_option"]
    obj.explanation = data.get("explanation") or ""
    obj.points = int(data["points"])
    if not edit_id:
        session.add(obj)
    session.commit()
    return obj


def _save_challenge(session, data, edit_id):
    obj = session.query(DailyChallenge).get(edit_id) if edit_id else DailyChallenge()
    obj.question_text = data["question_text"]
    obj.image_file_id = data.get("image_file_id")
    obj.option_a = data["option_a"]
    obj.option_b = data["option_b"]
    obj.option_c = data["option_c"]
    obj.option_d = data["option_d"]
    obj.correct_option = data["correct_option"]
    obj.explanation = data.get("explanation") or ""
    obj.is_active = True
    if not edit_id:
        session.add(obj)
    session.commit()
    return obj


SAVE_FUNCS = {
    "unit": _save_unit, "lesson": _save_lesson, "video": _save_video,
    "file": _save_file, "quiz": _save_quiz, "question": _save_question,
    "challenge": _save_challenge,
}


# ------------------------------------------------------------------ #
# عرض قائمة "إضافة محتوى"
# ------------------------------------------------------------------ #
@admin_only
async def show_add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await safe_edit(query, "➕ إضافة محتوى\n\nاختر نوع المحتوى الذي تريد إضافته:", reply_markup=add_menu_kb())


@admin_only
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /add - نفس قائمة إضافة المحتوى لكن عبر رسالة جديدة."""
    clear_conversation_state(context)
    await update.message.reply_text(
        "➕ إضافة محتوى\n\nاختر نوع المحتوى الذي تريد إضافته:", reply_markup=add_menu_kb()
    )


@admin_only
async def start_add_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    form_type = query.data.split("_", 1)[1]  # addnew_unit -> unit
    if form_type not in SAVE_FUNCS:
        await query.answer("نوع محتوى غير معروف.", show_alert=True)
        return
    clear_conversation_state(context)
    start_form(context, form_type)
    context.user_data["awaiting"] = AWAITING_FORM
    await _ask_current_field(update, context, via_query=query)


async def _ask_current_field(update: Update, context: ContextTypes.DEFAULT_TYPE, via_query=None):
    session = get_session()
    try:
        field = get_current_field(context)
        if field is None:
            form_type = context.user_data[FORM_TYPE_KEY]
            data = context.user_data[FORM_DATA_KEY]
            summary = summarize_form(form_type, data)
            from kb_admin import confirm_kb
            kb = confirm_kb("fconfirm", "fcancel")
            if via_query:
                await safe_edit(via_query, summary, reply_markup=kb)
            else:
                await update.message.reply_text(summary, reply_markup=kb)
            return

        text, kb = build_field_prompt(session, field)
        if via_query:
            await safe_edit(via_query, text, reply_markup=kb)
        else:
            await update.message.reply_text(text, reply_markup=kb)
    finally:
        session.close()


def _in_form(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data.get("awaiting") == AWAITING_FORM and FORM_TYPE_KEY in context.user_data


async def handle_form_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _in_form(context):
        return
    field = get_current_field(context)
    if field is None or field["type"] not in ("text", "int", "video_or_url"):
        return

    value = update.message.text.strip()

    if field["type"] == "int":
        if not value.lstrip("-").isdigit():
            await update.message.reply_text("⚠️ الرجاء إدخال رقم صحيح.")
            return
        store_value(context, field["key"], int(value))
    elif field["type"] == "video_or_url":
        store_value(context, field["key"], {"file_id": None, "url": value})
    else:
        store_value(context, field["key"], value)

    advance_field(context)
    await _ask_current_field(update, context)


async def handle_form_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _in_form(context):
        return
    field = get_current_field(context)
    if field is None or field["type"] != "photo":
        return
    file_id = update.message.photo[-1].file_id
    store_value(context, field["key"], file_id)
    advance_field(context)
    await _ask_current_field(update, context)


async def handle_form_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _in_form(context):
        return
    field = get_current_field(context)
    if field is None or field["type"] != "document":
        return
    file_id = update.message.document.file_id
    store_value(context, field["key"], file_id)
    advance_field(context)
    await _ask_current_field(update, context)


async def handle_form_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _in_form(context):
        return
    field = get_current_field(context)
    if field is None or field["type"] != "video_or_url":
        return
    file_id = update.message.video.file_id
    store_value(context, field["key"], {"file_id": file_id, "url": None})
    advance_field(context)
    await _ask_current_field(update, context)


async def handle_form_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not _in_form(context):
        await query.answer()
        return

    data = query.data

    if data == "fcancel":
        await query.answer()
        clear_form(context)
        context.user_data.pop("awaiting", None)
        await safe_edit(query, "❌ تم إلغاء العملية.", reply_markup=add_menu_kb())
        return

    if data == "fskip":
        field = get_current_field(context)
        await query.answer()
        if field and not field.get("required", True):
            store_value(context, field["key"], None)
            advance_field(context)
            await _ask_current_field(update, context, via_query=query)
        return

    if data.startswith("fval_"):
        field = get_current_field(context)
        if field is None:
            await query.answer()
            return
        raw = data[len("fval_"):]
        await query.answer()
        store_value(context, field["key"], raw)
        advance_field(context)
        await _ask_current_field(update, context, via_query=query)
        return

    if data == "fconfirm":
        if is_locked(context):
            await query.answer("جارٍ الحفظ...", show_alert=False)
            return
        set_lock(context, True)
        await query.answer()
        try:
            form_type = context.user_data[FORM_TYPE_KEY]
            edit_id = context.user_data.get(FORM_EDIT_ID_KEY)
            form_data = context.user_data[FORM_DATA_KEY]

            session = get_session()
            try:
                SAVE_FUNCS[form_type](session, form_data, edit_id)
                log_admin_action(
                    session, update.effective_user.id,
                    f"{'edit' if edit_id else 'add'}_{form_type}",
                    str(form_data),
                )
            finally:
                session.close()

            clear_form(context)
            context.user_data.pop("awaiting", None)
            action_word = "تعديل" if edit_id else "إنشاء"
            await safe_edit(
                query, f"✅ تم {action_word} العنصر بنجاح.",
                reply_markup=add_menu_kb(),
            )
        finally:
            set_lock(context, False)
        return
