"""
أوامر مشتركة بين الطالب والإدارة.
"""
from telegram import Update
from telegram.ext import ContextTypes

from utils_helpers import clear_conversation_state
from utils_forms import clear_form


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_conversation_state(context)
    clear_form(context)
    context.user_data.pop("awaiting", None)
    context.user_data.pop("active_quiz", None)
    await update.message.reply_text("❌ تم إلغاء العملية الحالية. اكتب /start للعودة للقائمة الرئيسية.")


async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أخطاء عام يمنع توقف البوت بالكامل بسبب خطأ في محادثة واحدة."""
    import logging
    logging.getLogger(__name__).exception("Unhandled exception", exc_info=context.error)
