"""
لوحات المفاتيح الخاصة بلوحة الإدارة.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def admin_panel_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("📚 إدارة الوحدات", callback_data="adm_units"),
         InlineKeyboardButton("📖 إدارة الدروس", callback_data="adm_lessons")],
        [InlineKeyboardButton("🎥 إدارة الفيديوهات", callback_data="adm_videos"),
         InlineKeyboardButton("📄 إدارة الملفات", callback_data="adm_files")],
        [InlineKeyboardButton("📝 إدارة الاختبارات", callback_data="adm_quizzes"),
         InlineKeyboardButton("🧮 إدارة الأسئلة", callback_data="adm_questions")],
        [InlineKeyboardButton("🔥 إدارة تحدي اليوم", callback_data="adm_challenge"),
         InlineKeyboardButton("👥 إدارة الطلاب", callback_data="adm_students")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="adm_stats"),
         InlineKeyboardButton("📢 إرسال إعلان", callback_data="adm_broadcast")],
        [InlineKeyboardButton("🏆 النقاط والإنجازات", callback_data="adm_achievements"),
         InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="adm_settings")],
        [InlineKeyboardButton("➕ إضافة محتوى", callback_data="add_menu")],
    ]
    return InlineKeyboardMarkup(rows)


def add_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("📚 إضافة وحدة", callback_data="addnew_unit")],
        [InlineKeyboardButton("📖 إضافة درس", callback_data="addnew_lesson")],
        [InlineKeyboardButton("🎥 إضافة فيديو", callback_data="addnew_video")],
        [InlineKeyboardButton("📄 إضافة ملف", callback_data="addnew_file")],
        [InlineKeyboardButton("📝 إضافة اختبار", callback_data="addnew_quiz")],
        [InlineKeyboardButton("🧮 إضافة سؤال", callback_data="addnew_question")],
        [InlineKeyboardButton("🔥 إضافة تحدي", callback_data="addnew_challenge")],
        [InlineKeyboardButton("⬅️ رجوع للوحة الإدارة", callback_data="admin_home")],
    ]
    return InlineKeyboardMarkup(rows)


def confirm_kb(yes_cb: str, no_cb: str = "admin_home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ نعم", callback_data=yes_cb),
         InlineKeyboardButton("❌ إلغاء", callback_data=no_cb)]
    ])


def cancel_only_kb(cb="admin_home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data=cb)]])


def items_manage_kb(items, prefix: str, page: int, total_pages: int, extra_back="admin_home") -> InlineKeyboardMarkup:
    """قائمة عناصر (وحدات/دروس/...) مع أزرار تعديل/حذف لكل عنصر."""
    rows = []
    for item in items:
        name = (
            getattr(item, "name", None)
            or getattr(item, "text", None)
            or getattr(item, "question_text", None)
            or f"#{item.id}"
        )
        name = str(name)[:40]
        status = "🟢" if getattr(item, "is_published", True) else "🟡"
        rows.append([
            InlineKeyboardButton(f"{status} {name}", callback_data=f"{prefix}_view_{item.id}"),
            InlineKeyboardButton("✏️", callback_data=f"{prefix}_edit_{item.id}"),
            InlineKeyboardButton("🗑️", callback_data=f"{prefix}_del_{item.id}"),
        ])
    nav = []
    if total_pages > 1:
        if page > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"{prefix}_page_{page-1}"))
        nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"{prefix}_page_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("➕ إضافة جديد", callback_data=f"addnew_{prefix}")])
    rows.append([InlineKeyboardButton("⬅️ رجوع", callback_data=extra_back)])
    return InlineKeyboardMarkup(rows)


def publish_toggle_kb(prefix: str, item_id: int, is_published: bool) -> InlineKeyboardMarkup:
    label = "🟡 تحويل لمسودة" if is_published else "🟢 نشر الآن"
    rows = [
        [InlineKeyboardButton(label, callback_data=f"{prefix}_toggle_{item_id}")],
        [InlineKeyboardButton("✏️ تعديل", callback_data=f"{prefix}_edit_{item_id}"),
         InlineKeyboardButton("🗑️ حذف", callback_data=f"{prefix}_del_{item_id}")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data=f"adm_{prefix}s")],
    ]
    return InlineKeyboardMarkup(rows)
