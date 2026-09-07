"""
إدارة المحتوى الموجود: عرض القوائم، التعديل، الحذف مع تأكيد.
مبني بشكل عام على PREFIX_MODEL بحيث يخدم كل أنواع المحتوى بنفس المنطق.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db_core import get_session
from db_models import Unit, Lesson, Video, FileItem, Quiz, Question, DailyChallenge
from db_crud import log_admin_action
from kb_admin import items_manage_kb, confirm_kb
from utils_decorators import admin_only
from utils_helpers import safe_edit, paginate
from utils_forms import start_form, FORM_DATA_KEY

PREFIX_MODEL = {
    "unit": Unit, "lesson": Lesson, "video": Video,
    "file": FileItem, "quiz": Quiz, "question": Question,
    "challenge": DailyChallenge,
}
PREFIX_TITLES = {
    "unit": "📚 الوحدات", "lesson": "📖 الدروس", "video": "🎥 الفيديوهات",
    "file": "📄 الملفات", "quiz": "📝 الاختبارات", "question": "🧮 الأسئلة",
    "challenge": "🔥 تحديات اليوم",
}
ORDER_FIELD = {
    "unit": Unit.order, "lesson": Lesson.order, "video": Video.order,
}
CALLBACK_TO_PREFIX = {
    "adm_units": "unit", "adm_lessons": "lesson", "adm_videos": "video",
    "adm_files": "file", "adm_quizzes": "quiz", "adm_questions": "question",
    "adm_challenge": "challenge",
}
PREFIX_TO_CALLBACK = {v: k for k, v in CALLBACK_TO_PREFIX.items()}


def _list_callback(prefix: str) -> str:
    return PREFIX_TO_CALLBACK.get(prefix, f"adm_{prefix}s")


def _query_items(session, prefix):
    model = PREFIX_MODEL[prefix]
    q = session.query(model)
    if prefix in ORDER_FIELD:
        q = q.order_by(ORDER_FIELD[prefix])
    else:
        q = q.order_by(model.id.desc())
    return q.all()


async def _render_list(query, prefix: str, page: int = 0):
    session = get_session()
    try:
        items = _query_items(session, prefix)
        title = PREFIX_TITLES.get(prefix, prefix)
        if not items:
            await safe_edit(
                query, f"{title}\n\n📭 لا توجد عناصر بعد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ إضافة جديد", callback_data=f"addnew_{prefix}")],
                    [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_home")],
                ]),
            )
            return
        page_items, total_pages = paginate(items, page, page_size=8)
        await safe_edit(
            query, f"{title}\n\nاختر عنصراً للعرض، أو استخدم ✏️ / 🗑️:",
            reply_markup=items_manage_kb(page_items, prefix, page, total_pages),
        )
    finally:
        session.close()


@admin_only
async def show_manage_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    await query.answer()
    prefix = CALLBACK_TO_PREFIX.get(query.data, query.data.split("_")[0])
    await _render_list(query, prefix, page)


async def manage_list_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")  # {prefix}_page_{n}
    prefix, page = parts[0], int(parts[-1])
    await _render_list(query, prefix, page)


@admin_only
async def view_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")  # {prefix}_view_{id}
    prefix, item_id = parts[0], int(parts[-1])
    session = get_session()
    try:
        model = PREFIX_MODEL[prefix]
        item = session.query(model).get(item_id)
        if not item:
            await query.answer("العنصر غير موجود.", show_alert=True)
            return
        lines = [f"🔎 تفاصيل العنصر (#{item.id})\n"]
        for col in model.__table__.columns:
            val = getattr(item, col.name)
            lines.append(f"• {col.name}: {val}")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ تعديل", callback_data=f"{prefix}_edit_{item_id}"),
             InlineKeyboardButton("🗑️ حذف", callback_data=f"{prefix}_del_{item_id}")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data=_list_callback(prefix))],
        ])
        await safe_edit(query, "\n".join(lines)[:4000], reply_markup=kb)
    finally:
        session.close()


@admin_only
async def start_edit_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from h_admin_add_content import _ask_current_field, AWAITING_FORM
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")  # {prefix}_edit_{id}
    prefix, item_id = parts[0], int(parts[-1])

    start_form(context, prefix, edit_id=item_id)
    context.user_data["awaiting"] = AWAITING_FORM
    await _ask_current_field(update, context, via_query=query)


@admin_only
async def confirm_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")  # {prefix}_del_{id}
    prefix, item_id = parts[0], int(parts[-1])
    text = "⚠️ هل أنت متأكد من الحذف؟ لا يمكن التراجع عن هذا الإجراء."
    await safe_edit(query, text, reply_markup=confirm_kb(f"{prefix}_delok_{item_id}", _list_callback(prefix)))


@admin_only
async def do_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split("_")  # {prefix}_delok_{id}
    prefix, item_id = parts[0], int(parts[-1])
    session = get_session()
    try:
        model = PREFIX_MODEL[prefix]
        item = session.query(model).get(item_id)
        if item:
            session.delete(item)
            session.commit()
            log_admin_action(session, update.effective_user.id, f"delete_{prefix}", f"id={item_id}")
        await query.answer("🗑️ تم الحذف.")
    finally:
        session.close()
    await _render_list(query, prefix, 0)
