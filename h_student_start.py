"""
أمر /start والقائمة الرئيسية.
"""
from telegram import Update
from telegram.ext import ContextTypes

from db_core import get_session
from db_crud import get_or_create_user
from kb_student import main_menu_kb
from config import BOT_DISPLAY_NAME, BOT_SLOGAN
from utils_helpers import safe_edit, clear_conversation_state

WELCOME_TEXT = (
    "{title}\n"
    "رياضيات | السنة الثانية ثانوي\n\n"
    "👋 أهلاً بك يا {name}\n\n"
    "{slogan}"
)


def build_welcome_text(name: str) -> str:
    return WELCOME_TEXT.format(title=BOT_DISPLAY_NAME, name=name, slogan=BOT_SLOGAN)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_conversation_state(context)
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        text = build_welcome_text(user.full_name or update.effective_user.first_name)
        await update.message.reply_text(text, reply_markup=main_menu_kb())
    finally:
        session.close()


async def home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_conversation_state(context)
    query = update.callback_query
    await query.answer()
    session = get_session()
    try:
        user = get_or_create_user(session, update.effective_user)
        text = build_welcome_text(user.full_name or update.effective_user.first_name)
        await safe_edit(query, text, reply_markup=main_menu_kb())
    finally:
        session.close()


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """زر معطل (مثل رقم الصفحة) - فقط يرد على الضغطة بدون أي تغيير."""
    await update.callback_query.answer()
