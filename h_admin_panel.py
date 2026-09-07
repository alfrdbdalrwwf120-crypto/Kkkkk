"""
/admin - نقطة الدخول للوحة الإدارة.
"""
from telegram import Update
from telegram.ext import ContextTypes

from kb_admin import admin_panel_kb
from utils_decorators import admin_only
from utils_helpers import safe_edit, clear_conversation_state


@admin_only
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_conversation_state(context)
    await update.message.reply_text("⚙️ لوحة الإدارة", reply_markup=admin_panel_kb())


@admin_only
async def admin_home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_conversation_state(context)
    query = update.callback_query
    await query.answer()
    await safe_edit(query, "⚙️ لوحة الإدارة", reply_markup=admin_panel_kb())
