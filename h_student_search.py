"""
🔍 البحث الداخلي
"""
from telegram import Update
from telegram.ext import ContextTypes

from db_core import get_session
from db_crud import search_content
from kb_student import back_home_kb, cancel_kb
from utils_helpers import safe_edit

SEARCH_STATE = "search"


async def prompt_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting"] = SEARCH_STATE
    await safe_edit(
        query,
        "🔍 اكتب كلمة أو جملة للبحث عنها\n(درس، وحدة، فيديو، ملف، اختبار):",
        reply_markup=cancel_kb("home"),
    )


async def handle_search_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("awaiting", None)
    term = update.message.text.strip()
    if len(term) < 2:
        await update.message.reply_text("الرجاء كتابة كلمة أطول للبحث.")
        return

    session = get_session()
    try:
        results = search_content(session, term)
        total = sum(len(v) for v in results.values())
        if total == 0:
            await update.message.reply_text(
                f"📭 لم يتم العثور على نتائج لـ: {term}", reply_markup=back_home_kb()
            )
            return

        lines = [f"🔍 نتائج البحث عن: {term}\n"]
        labels = {
            "units": "📚 وحدات", "lessons": "📖 دروس", "videos": "🎥 فيديوهات",
            "files": "📄 ملفات", "quizzes": "📝 اختبارات",
        }
        for key, label in labels.items():
            items = results[key]
            if items:
                lines.append(f"{label}:")
                for it in items[:5]:
                    lines.append(f"  • {it.name}")
                lines.append("")

        await update.message.reply_text("\n".join(lines), reply_markup=back_home_kb())
    finally:
        session.close()
