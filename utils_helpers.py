"""
دوال مساعدة عامة تُستخدم في كل أنحاء البوت:
- رسم شريط تقدّم نصي
- تقسيم القوائم الطويلة لصفحات (Pagination)
- تعديل الرسالة بأمان بدل إعادة إرسالها (لضمان السلاسة وعدم تكرار الرسائل)
- قفل بسيط لمنع تكرار الضغط على الأزرار أثناء العمليات الحساسة
"""
import asyncio
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from config import PAGE_SIZE


def progress_bar(percent: int, length: int = 10) -> str:
    percent = max(0, min(100, percent))
    filled = round(length * percent / 100)
    return "▓" * filled + "░" * (length - filled) + f"  {percent}%"


def paginate(items: list, page: int, page_size: int = PAGE_SIZE):
    """يرجع (العناصر في الصفحة الحالية, إجمالي عدد الصفحات)."""
    if not items:
        return [], 1
    total_pages = max(1, (len(items) + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    return items[start:start + page_size], total_pages


async def safe_edit(query, text: str, reply_markup=None, parse_mode=None):
    """يحاول تعديل الرسالة الحالية، وإن تعذّر (رسالة قديمة/وسائط) يرسل رسالة جديدة."""
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            return
        try:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception:
            pass


def is_locked(context: ContextTypes.DEFAULT_TYPE) -> bool:
    """يمنع تكرار الضغط على أزرار الإنشاء/الحذف قبل انتهاء العملية السابقة."""
    return context.user_data.get("_processing", False)


def set_lock(context: ContextTypes.DEFAULT_TYPE, value: bool):
    context.user_data["_processing"] = value


def clear_conversation_state(context: ContextTypes.DEFAULT_TYPE):
    """يمسح أي بيانات مؤقتة لمحادثة إضافة/تعديل محتوى (يُستخدم عند الإلغاء)."""
    for key in list(context.user_data.keys()):
        if key.startswith("form_") or key == "_processing":
            del context.user_data[key]
