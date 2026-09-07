"""
محرّك نماذج عام يقود كل عمليات "إضافة/تعديل" في لوحة الإدارة اعتماداً على
وصف (schema) لكل نوع محتوى. هذا هو ما يجعل إضافة نوع محتوى جديد مستقبلاً
مجرد إضافة قاموس جديد في FORM_SCHEMAS دون كتابة أي منطق محادثة إضافي.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from db_core import get_session
from db_models import Unit, Lesson, Quiz

FORM_DATA_KEY = "form_data"
FORM_TYPE_KEY = "form_type"
FORM_FIELD_IDX_KEY = "form_field_idx"
FORM_EDIT_ID_KEY = "form_edit_id"


# ------------------------------------------------------------------ #
# تعريف الحقول لكل نوع محتوى
# ------------------------------------------------------------------ #
FORM_SCHEMAS = {
    "unit": [
        dict(key="name", label="اسم الوحدة", type="text", required=True),
        dict(key="description", label="وصف الوحدة", type="text", required=False),
        dict(key="order", label="رقم وترتيب الوحدة (مثال: 1)", type="int", required=True),
        dict(key="image_file_id", label="صورة الوحدة", type="photo", required=False),
        dict(key="is_published", label="حالة النشر", type="bool_publish", required=True),
    ],
    "lesson": [
        dict(key="unit_id", label="اختر الوحدة", type="select_unit", required=True),
        dict(key="name", label="اسم الدرس", type="text", required=True),
        dict(key="description", label="وصف الدرس", type="text", required=False),
        dict(key="content_text", label="الشرح المكتوب", type="text", required=False),
        dict(key="order", label="ترتيب الدرس داخل الوحدة (مثال: 1)", type="int", required=True),
        dict(key="is_published", label="حالة النشر", type="bool_publish", required=True),
    ],
    "video": [
        dict(key="lesson_id", label="اختر الدرس", type="select_lesson", required=True),
        dict(key="name", label="اسم الفيديو", type="text", required=True),
        dict(key="description", label="وصف الفيديو", type="text", required=False),
        dict(key="video", label="أرسل الفيديو نفسه، أو الصق رابطه", type="video_or_url", required=True),
        dict(key="order", label="ترتيب الفيديو (مثال: 1)", type="int", required=True),
        dict(key="is_published", label="حالة النشر", type="bool_publish", required=True),
    ],
    "file": [
        dict(key="unit_id", label="اختر الوحدة", type="select_unit", required=True),
        dict(key="lesson_id", label="اختر الدرس (أو تخطَّ لربطه بالوحدة فقط)", type="select_lesson_optional", required=False),
        dict(key="name", label="اسم الملف", type="text", required=True),
        dict(key="document", label="أرسل الملف", type="document", required=True),
        dict(key="description", label="وصف الملف", type="text", required=False),
        dict(key="file_type", label="نوع الملف", type="file_type_select", required=True),
        dict(key="is_published", label="حالة النشر", type="bool_publish", required=True),
    ],
    "quiz": [
        dict(key="name", label="اسم الاختبار", type="text", required=True),
        dict(key="quiz_type", label="نوع الاختبار", type="quiz_type_select", required=True),
        dict(key="unit_id", label="اختر الوحدة (أو تخطَّ)", type="select_unit_optional", required=False),
        dict(key="lesson_id", label="اختر الدرس (أو تخطَّ)", type="select_lesson_optional", required=False),
        dict(key="duration_minutes", label="مدة الاختبار بالدقائق (0 = بلا وقت محدد)", type="int", required=True),
        dict(key="pass_score", label="درجة النجاح % (مثال: 50)", type="int", required=True),
        dict(key="is_published", label="حالة النشر", type="bool_publish", required=True),
    ],
    "question": [
        dict(key="quiz_id", label="اختر الاختبار", type="select_quiz", required=True),
        dict(key="text", label="نص السؤال", type="text", required=True),
        dict(key="image_file_id", label="صورة السؤال", type="photo", required=False),
        dict(key="option_a", label="الخيار A", type="text", required=True),
        dict(key="option_b", label="الخيار B", type="text", required=True),
        dict(key="option_c", label="الخيار C", type="text", required=True),
        dict(key="option_d", label="الخيار D", type="text", required=True),
        dict(key="correct_option", label="الإجابة الصحيحة", type="option_letter", required=True),
        dict(key="explanation", label="شرح الإجابة", type="text", required=False),
        dict(key="points", label="الدرجة (رقم)", type="int", required=True),
    ],
    "challenge": [
        dict(key="question_text", label="نص سؤال التحدي", type="text", required=True),
        dict(key="image_file_id", label="صورة السؤال", type="photo", required=False),
        dict(key="option_a", label="الخيار A", type="text", required=True),
        dict(key="option_b", label="الخيار B", type="text", required=True),
        dict(key="option_c", label="الخيار C", type="text", required=True),
        dict(key="option_d", label="الخيار D", type="text", required=True),
        dict(key="correct_option", label="الإجابة الصحيحة", type="option_letter", required=True),
        dict(key="explanation", label="شرح الإجابة", type="text", required=False),
    ],
}

TYPE_TITLES = {
    "unit": "📚 وحدة", "lesson": "📖 درس", "video": "🎥 فيديو",
    "file": "📄 ملف", "quiz": "📝 اختبار", "question": "🧮 سؤال",
    "challenge": "🔥 تحدي",
}

FILE_TYPE_OPTIONS = [
    ("pdf", "📕 PDF"), ("summary", "📝 ملخص"), ("worksheet", "📄 ورقة عمل"),
    ("exercises", "✏️ تمارين"), ("review", "🔁 مراجعة"), ("exam", "🧾 نموذج امتحان"),
]
QUIZ_TYPE_OPTIONS = [
    ("quick", "⚡ اختبار سريع"), ("lesson", "📖 اختبار درس"),
    ("unit", "📐 اختبار وحدة"), ("comprehensive", "🧾 اختبار شامل"),
]


def start_form(context: ContextTypes.DEFAULT_TYPE, form_type: str, edit_id: int | None = None,
               initial_data: dict | None = None):
    context.user_data[FORM_TYPE_KEY] = form_type
    context.user_data[FORM_DATA_KEY] = dict(initial_data or {})
    context.user_data[FORM_FIELD_IDX_KEY] = 0
    context.user_data[FORM_EDIT_ID_KEY] = edit_id


def get_current_field(context: ContextTypes.DEFAULT_TYPE):
    form_type = context.user_data.get(FORM_TYPE_KEY)
    idx = context.user_data.get(FORM_FIELD_IDX_KEY, 0)
    schema = FORM_SCHEMAS.get(form_type, [])
    if idx >= len(schema):
        return None
    return schema[idx]


def advance_field(context: ContextTypes.DEFAULT_TYPE):
    context.user_data[FORM_FIELD_IDX_KEY] = context.user_data.get(FORM_FIELD_IDX_KEY, 0) + 1


def store_value(context: ContextTypes.DEFAULT_TYPE, key: str, value):
    context.user_data.setdefault(FORM_DATA_KEY, {})[key] = value


def is_form_complete(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return get_current_field(context) is None


def clear_form(context: ContextTypes.DEFAULT_TYPE):
    for k in (FORM_DATA_KEY, FORM_TYPE_KEY, FORM_FIELD_IDX_KEY, FORM_EDIT_ID_KEY):
        context.user_data.pop(k, None)


def _nav_row(field):
    row = []
    if not field.get("required", True):
        row.append(InlineKeyboardButton("⏭️ تخطي", callback_data="fskip"))
    row.append(InlineKeyboardButton("❌ إلغاء", callback_data="fcancel"))
    return row


def build_field_prompt(session, field: dict):
    """يرجع (نص الرسالة, InlineKeyboardMarkup أو None) للحقل الحالي."""
    label = field["label"]
    ftype = field["type"]
    text = f"✏️ {label}:"

    if ftype in ("text", "int"):
        return text, InlineKeyboardMarkup([_nav_row(field)])

    if ftype == "bool_publish":
        rows = [
            [InlineKeyboardButton("🟢 نشر الآن", callback_data="fval_1"),
             InlineKeyboardButton("🟡 حفظ كمسودة", callback_data="fval_0")],
            _nav_row(field),
        ]
        return text, InlineKeyboardMarkup(rows)

    if ftype == "option_letter":
        rows = [
            [InlineKeyboardButton("A", callback_data="fval_A"),
             InlineKeyboardButton("B", callback_data="fval_B"),
             InlineKeyboardButton("C", callback_data="fval_C"),
             InlineKeyboardButton("D", callback_data="fval_D")],
            _nav_row(field),
        ]
        return text, InlineKeyboardMarkup(rows)

    if ftype == "file_type_select":
        rows = [[InlineKeyboardButton(label_, callback_data=f"fval_{code}")]
                for code, label_ in FILE_TYPE_OPTIONS]
        rows.append(_nav_row(field))
        return text, InlineKeyboardMarkup(rows)

    if ftype == "quiz_type_select":
        rows = [[InlineKeyboardButton(label_, callback_data=f"fval_{code}")]
                for code, label_ in QUIZ_TYPE_OPTIONS]
        rows.append(_nav_row(field))
        return text, InlineKeyboardMarkup(rows)

    if ftype in ("select_unit", "select_unit_optional"):
        units = session.query(Unit).order_by(Unit.order).all()
        rows = [[InlineKeyboardButton(u.name, callback_data=f"fval_{u.id}")] for u in units]
        rows.append(_nav_row(field))
        return text, InlineKeyboardMarkup(rows)

    if ftype in ("select_lesson", "select_lesson_optional"):
        lessons = session.query(Lesson).order_by(Lesson.unit_id, Lesson.order).all()
        rows = [
            [InlineKeyboardButton(f"{l.unit.name} › {l.name}", callback_data=f"fval_{l.id}")]
            for l in lessons
        ]
        rows.append(_nav_row(field))
        return text, InlineKeyboardMarkup(rows)

    if ftype == "select_quiz":
        quizzes = session.query(Quiz).all()
        rows = [[InlineKeyboardButton(q.name, callback_data=f"fval_{q.id}")] for q in quizzes]
        rows.append(_nav_row(field))
        return text, InlineKeyboardMarkup(rows)

    if ftype == "photo":
        return text + "\n(أرسل صورة)", InlineKeyboardMarkup([_nav_row(field)])

    if ftype == "video_or_url":
        return text, InlineKeyboardMarkup([_nav_row(field)])

    if ftype == "document":
        return text + "\n(أرسل الملف كـ Document)", InlineKeyboardMarkup([_nav_row(field)])

    return text, InlineKeyboardMarkup([_nav_row(field)])


def summarize_form(form_type: str, data: dict) -> str:
    schema = FORM_SCHEMAS[form_type]
    lines = [f"📋 مراجعة {TYPE_TITLES.get(form_type, form_type)} قبل الحفظ:\n"]
    for field in schema:
        val = data.get(field["key"])
        if val in (None, ""):
            val = "—"
        lines.append(f"• {field['label']}: {val}")
    return "\n".join(lines)
