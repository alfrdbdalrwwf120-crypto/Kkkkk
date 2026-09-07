"""
لوحات المفاتيح (Inline Keyboards) الخاصة بواجهة الطالب.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

HOME_ROW = [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]


def main_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("📚 ابدأ الدراسة", callback_data="study")],
        [InlineKeyboardButton("🎥 آخر الدروس", callback_data="continue_last"),
         InlineKeyboardButton("📝 الاختبارات", callback_data="quizzes_menu")],
        [InlineKeyboardButton("🧠 اسأل أطلس", callback_data="ask_atlas"),
         InlineKeyboardButton("🔥 تحدي اليوم", callback_data="daily_challenge")],
        [InlineKeyboardButton("📊 تقدمي", callback_data="my_progress"),
         InlineKeyboardButton("🏆 إنجازاتي", callback_data="my_achievements")],
        [InlineKeyboardButton("📖 مكتبتي", callback_data="library"),
         InlineKeyboardButton("🔍 البحث", callback_data="search")],
        [InlineKeyboardButton("📢 الإعلانات", callback_data="announcements"),
         InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(rows)


def back_home_kb(back_cb: str | None = None) -> InlineKeyboardMarkup:
    row = []
    if back_cb:
        row.append(InlineKeyboardButton("⬅️ رجوع", callback_data=back_cb))
    row.append(InlineKeyboardButton("🏠 الرئيسية", callback_data="home"))
    return InlineKeyboardMarkup([row])


def units_list_kb(units_page, page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"📐 {u.name}", callback_data=f"unit_{u.id}_0")] for u in units_page]
    nav = []
    if total_pages > 1:
        if page > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"study_page_{page-1}"))
        nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"study_page_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append(HOME_ROW)
    return InlineKeyboardMarkup(rows)


def unit_lessons_kb(unit_id, lessons_page, page, total_pages, status_map, unit_quiz=None) -> InlineKeyboardMarkup:
    rows = []
    for l in lessons_page:
        icon = "✅" if status_map.get(l.id) == "completed" else "▶️"
        rows.append([InlineKeyboardButton(f"{icon} {l.name}", callback_data=f"lesson_{l.id}")])
    nav = []
    if total_pages > 1:
        if page > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"unit_{unit_id}_{page-1}"))
        nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"unit_{unit_id}_{page+1}"))
    if nav:
        rows.append(nav)
    if unit_quiz:
        rows.append([InlineKeyboardButton("📝 اختبار الوحدة", callback_data=f"quiz_start_{unit_quiz.id}")])
    rows.append([InlineKeyboardButton("⬅️ رجوع", callback_data="study"),
                 InlineKeyboardButton("🏠 الرئيسية", callback_data="home")])
    return InlineKeyboardMarkup(rows)


def lesson_page_kb(lesson, has_video, has_files, quiz, prev_id, next_id) -> InlineKeyboardMarkup:
    rows = []
    if has_video:
        rows.append([InlineKeyboardButton("🎥 مشاهدة الشرح", callback_data=f"lvideo_{lesson.id}")])
    rows.append([InlineKeyboardButton("📖 الشرح المكتوب", callback_data=f"ltext_{lesson.id}")])
    rows.append([InlineKeyboardButton("🧮 الأمثلة المحلولة", callback_data=f"lexamples_{lesson.id}")])
    rows.append([InlineKeyboardButton("✏️ التمارين", callback_data=f"lexercises_{lesson.id}")])
    if quiz:
        rows.append([InlineKeyboardButton("📝 اختبار الدرس", callback_data=f"quiz_start_{quiz.id}")])
    if has_files:
        rows.append([InlineKeyboardButton("📄 تحميل الملخص", callback_data=f"lfiles_{lesson.id}")])

    nav = []
    if prev_id:
        nav.append(InlineKeyboardButton("⬅️ الدرس السابق", callback_data=f"lesson_{prev_id}"))
    if next_id:
        nav.append(InlineKeyboardButton("➡️ الدرس التالي", callback_data=f"lesson_{next_id}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("✅ تم إكمال الدرس", callback_data=f"lcomplete_{lesson.id}")])
    rows.append([InlineKeyboardButton("⬅️ رجوع للوحدة", callback_data=f"unit_{lesson.unit_id}_0"),
                 InlineKeyboardButton("🏠 الرئيسية", callback_data="home")])
    return InlineKeyboardMarkup(rows)


def quiz_question_kb(quiz_id, q_index, question) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"A) {question.option_a}", callback_data=f"qans_{quiz_id}_{q_index}_A")],
        [InlineKeyboardButton(f"B) {question.option_b}", callback_data=f"qans_{quiz_id}_{q_index}_B")],
        [InlineKeyboardButton(f"C) {question.option_c}", callback_data=f"qans_{quiz_id}_{q_index}_C")],
        [InlineKeyboardButton(f"D) {question.option_d}", callback_data=f"qans_{quiz_id}_{q_index}_D")],
        [InlineKeyboardButton("❌ إلغاء الاختبار", callback_data="home")],
    ]
    return InlineKeyboardMarkup(rows)


def quiz_result_kb(quiz_id) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🔁 إعادة الاختبار", callback_data=f"quiz_start_{quiz_id}")],
        HOME_ROW,
    ]
    return InlineKeyboardMarkup(rows)


def daily_challenge_kb(challenge_id, challenge) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"A) {challenge.option_a}", callback_data=f"dcans_{challenge_id}_A")],
        [InlineKeyboardButton(f"B) {challenge.option_b}", callback_data=f"dcans_{challenge_id}_B")],
        [InlineKeyboardButton(f"C) {challenge.option_c}", callback_data=f"dcans_{challenge_id}_C")],
        [InlineKeyboardButton(f"D) {challenge.option_d}", callback_data=f"dcans_{challenge_id}_D")],
        HOME_ROW,
    ]
    return InlineKeyboardMarkup(rows)


def cancel_kb(back_cb="home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data=back_cb)]])
