"""
🎓 أطلس 2010 | رياضيات 2 ثانوي
نقطة تشغيل البوت الرئيسية - تسجيل كل الـ handlers.
"""
import logging
import http.server, threading
threading.Thread(target=lambda: http.server.HTTPServer(("0.0.0.0", int(__import__("os").environ.get("PORT", 3000))), http.server.BaseHTTPRequestHandler).serve_forever(), daemon=True).start()

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters,
    PicklePersistence,
)

from config import BOT_TOKEN
from db_core import init_db

from h_common import cancel_command, error_handler
import h_student_start as h_start
import h_student_study as h_study
import h_student_quiz as h_quiz
import h_student_ask_atlas as h_ask
import h_student_challenge as h_challenge
import h_student_progress as h_progress
import h_student_search as h_search
import h_student_misc as h_misc

import h_admin_panel as a_panel
import h_admin_add_content as a_add
import h_admin_manage_content as a_manage
import h_admin_stats as a_stats
import h_admin_broadcast as a_broadcast

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)


# ------------------------------------------------------------------ #
# موجّهات الرسائل النصية / الوسائط - كل حالة تُفعّل عبر context.user_data["awaiting"]
# ------------------------------------------------------------------ #
async def text_router(update: Update, context):
    awaiting = context.user_data.get("awaiting")
    if awaiting == h_ask.ASK_ATLAS_STATE:
        await h_ask.handle_ask_atlas_text(update, context)
    elif awaiting == h_search.SEARCH_STATE:
        await h_search.handle_search_text(update, context)
    elif awaiting == a_add.AWAITING_FORM:
        await a_add.handle_form_text(update, context)
    elif awaiting == a_broadcast.AWAITING_BROADCAST:
        await a_broadcast.handle_broadcast_text(update, context)
    # لا يوجد حالة نشطة: نتجاهل الرسالة بصمت لإبقاء البوت سلساً بلا ردود عشوائية


async def photo_router(update: Update, context):
    awaiting = context.user_data.get("awaiting")
    if awaiting == h_ask.ASK_ATLAS_STATE:
        await h_ask.handle_ask_atlas_photo(update, context)
    elif awaiting == a_add.AWAITING_FORM:
        await a_add.handle_form_photo(update, context)


async def document_router(update: Update, context):
    if context.user_data.get("awaiting") == a_add.AWAITING_FORM:
        await a_add.handle_form_document(update, context)


async def video_router(update: Update, context):
    if context.user_data.get("awaiting") == a_add.AWAITING_FORM:
        await a_add.handle_form_video(update, context)


def build_application() -> Application:
    persistence = PicklePersistence(filepath="atlas2010_bot_state.pickle")
    app = Application.builder().token(BOT_TOKEN).persistence(persistence).build()

    # ---------------- أوامر ---------------- #
    app.add_handler(CommandHandler("start", h_start.start_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("admin", a_panel.admin_command))
    app.add_handler(CommandHandler("add", a_add.add_command))

    # ---------------- أزرار الطالب ---------------- #
    app.add_handler(CallbackQueryHandler(h_start.home_callback, pattern=r"^home$"))
    app.add_handler(CallbackQueryHandler(h_start.noop_callback, pattern=r"^noop$"))

    app.add_handler(CallbackQueryHandler(h_study.show_study_menu, pattern=r"^study$"))
    app.add_handler(CallbackQueryHandler(h_study.study_page_callback, pattern=r"^study_page_\d+$"))
    app.add_handler(CallbackQueryHandler(h_study.show_unit, pattern=r"^unit_\d+_\d+$"))
    app.add_handler(CallbackQueryHandler(h_study.show_lesson, pattern=r"^lesson_\d+$"))
    app.add_handler(CallbackQueryHandler(h_study.send_lesson_video, pattern=r"^lvideo_\d+$"))
    app.add_handler(CallbackQueryHandler(h_study.send_lesson_text, pattern=r"^ltext_\d+$"))
    app.add_handler(CallbackQueryHandler(h_study.send_lesson_examples, pattern=r"^lexamples_\d+$"))
    app.add_handler(CallbackQueryHandler(h_study.send_lesson_exercises, pattern=r"^lexercises_\d+$"))
    app.add_handler(CallbackQueryHandler(h_study.send_lesson_files, pattern=r"^lfiles_\d+$"))
    app.add_handler(CallbackQueryHandler(h_study.complete_lesson, pattern=r"^lcomplete_\d+$"))
    app.add_handler(CallbackQueryHandler(h_study.continue_last_lesson, pattern=r"^continue_last$"))

    app.add_handler(CallbackQueryHandler(h_quiz.show_quizzes_menu, pattern=r"^quizzes_menu$"))
    app.add_handler(CallbackQueryHandler(h_quiz.quizzes_menu_page, pattern=r"^quizpage_\d+$"))
    app.add_handler(CallbackQueryHandler(h_quiz.start_quiz, pattern=r"^quiz_start_\d+$"))
    app.add_handler(CallbackQueryHandler(h_quiz.answer_question, pattern=r"^qans_\d+_\d+_[ABCD]$"))

    app.add_handler(CallbackQueryHandler(h_ask.prompt_ask_atlas, pattern=r"^ask_atlas$"))

    app.add_handler(CallbackQueryHandler(h_challenge.show_daily_challenge, pattern=r"^daily_challenge$"))
    app.add_handler(CallbackQueryHandler(h_challenge.answer_challenge, pattern=r"^dcans_\d+_[ABCD]$"))

    app.add_handler(CallbackQueryHandler(h_progress.show_my_progress, pattern=r"^my_progress$"))
    app.add_handler(CallbackQueryHandler(h_progress.show_my_achievements, pattern=r"^my_achievements$"))

    app.add_handler(CallbackQueryHandler(h_misc.show_library, pattern=r"^library$"))
    app.add_handler(CallbackQueryHandler(h_misc.show_library_unit_files, pattern=r"^lib_unit_\d+$"))
    app.add_handler(CallbackQueryHandler(h_misc.show_announcements, pattern=r"^announcements$"))
    app.add_handler(CallbackQueryHandler(h_misc.show_settings, pattern=r"^settings$"))
    app.add_handler(CallbackQueryHandler(h_misc.toggle_notifications, pattern=r"^toggle_notif$"))

    app.add_handler(CallbackQueryHandler(h_search.prompt_search, pattern=r"^search$"))

    # ---------------- أزرار الإدارة ---------------- #
    app.add_handler(CallbackQueryHandler(a_panel.admin_home_callback, pattern=r"^admin_home$"))
    app.add_handler(CallbackQueryHandler(a_add.show_add_menu, pattern=r"^add_menu$"))
    app.add_handler(CallbackQueryHandler(a_add.start_add_flow, pattern=r"^addnew_\w+$"))
    app.add_handler(CallbackQueryHandler(a_add.handle_form_callback, pattern=r"^f(val_.*|skip|cancel|confirm)$"))

    app.add_handler(CallbackQueryHandler(
        a_manage.show_manage_list,
        pattern=r"^adm_(units|lessons|videos|files|quizzes|questions|challenge)$",
    ))
    app.add_handler(CallbackQueryHandler(
        a_manage.manage_list_page, pattern=r"^(unit|lesson|video|file|quiz|question|challenge)_page_\d+$"
    ))
    app.add_handler(CallbackQueryHandler(
        a_manage.view_item, pattern=r"^(unit|lesson|video|file|quiz|question|challenge)_view_\d+$"
    ))
    app.add_handler(CallbackQueryHandler(
        a_manage.start_edit_item, pattern=r"^(unit|lesson|video|file|quiz|question|challenge)_edit_\d+$"
    ))
    app.add_handler(CallbackQueryHandler(
        a_manage.confirm_delete_item, pattern=r"^(unit|lesson|video|file|quiz|question|challenge)_del_\d+$"
    ))
    app.add_handler(CallbackQueryHandler(
        a_manage.do_delete_item, pattern=r"^(unit|lesson|video|file|quiz|question|challenge)_delok_\d+$"
    ))

    app.add_handler(CallbackQueryHandler(a_stats.show_stats, pattern=r"^adm_stats$"))
    app.add_handler(CallbackQueryHandler(a_stats.show_students, pattern=r"^adm_students$"))
    app.add_handler(CallbackQueryHandler(a_stats.show_students_page, pattern=r"^students_page_\d+$"))
    app.add_handler(CallbackQueryHandler(a_stats.show_achievements_admin, pattern=r"^adm_achievements$"))
    app.add_handler(CallbackQueryHandler(a_stats.show_bot_settings, pattern=r"^adm_settings$"))

    app.add_handler(CallbackQueryHandler(a_broadcast.show_broadcast_menu, pattern=r"^adm_broadcast$"))
    app.add_handler(CallbackQueryHandler(a_broadcast.choose_broadcast_type, pattern=r"^bctype_\w+$"))
    app.add_handler(CallbackQueryHandler(a_broadcast.send_broadcast, pattern=r"^bcsend$"))

    # ---------------- الرسائل (نص / صورة / ملف / فيديو) ---------------- #
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_handler(MessageHandler(filters.PHOTO, photo_router))
    app.add_handler(MessageHandler(filters.Document.ALL, document_router))
    app.add_handler(MessageHandler(filters.VIDEO, video_router))

    app.add_error_handler(error_handler)
    return app


def main():
    init_db()
    app = build_application()
    print("🎓 أطلس 2010 يعمل الآن...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
