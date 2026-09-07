"""
ديكوريتورز مشتركة - أهمها التحقق من صلاحية الإدارة.
"""
import functools
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS


def admin_only(handler):
    """يمنع أي مستخدم غير موجود في ADMIN_IDS من تنفيذ الأمر/الزر."""
    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id not in ADMIN_IDS:
            if update.callback_query:
                await update.callback_query.answer(
                    "⛔ هذا القسم مخصص للإدارة فقط.", show_alert=True
                )
            elif update.message:
                await update.message.reply_text("⛔ هذا القسم مخصص للإدارة فقط.")
            return
        return await handler(update, context, *args, **kwargs)
    return wrapper
