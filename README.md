# 🎓 أطلس 2010 | رياضيات 2 ثانوي — نسخة جاهزة للرفع من الجوال

⚠️ **هذه نسخة معدّلة** من المشروع الأصلي: كل الملفات وُضعت في مجلد واحد (بدون مجلدات فرعية)
حتى يسهل رفعها من متصفح الجوال على GitHub (الذي لا يدعم رفع المجلدات مباشرة).
تم تعديل كل أسطر `import` داخل الملفات لتتوافق مع هذا الترتيب الجديد. وظيفة
البوت لم تتغيّر أبداً — فقط ترتيب الملفات.

## ✅ لا يوجد ملف SQL لتنفيذه يدوياً

هذا المشروع يستخدم SQLAlchemy، وهو يُنشئ كل الجداول **تلقائياً** أول ما
يشتغل البوت (داخل دالة `init_db()` في `db_core.py`). كل ما تحتاجه هو رابط
اتصال صحيح بقاعدة بيانات، وليس نسخ ولصق أي كود SQL.

## 🗄️ الخطوة 1: أنشئ مشروع Supabase منفصل (يُفضّل)

هذا بوت مختلف تماماً عن بوت التصميم، فمن الأفضل أن يكون له مشروع Supabase
خاص به حتى لا تختلط بياناتهما:

1. [supabase.com](https://supabase.com) → **New project**
2. اسم المشروع: `atlas2010-bot` (أو أي اسم)
3. اختر كلمة مرور لقاعدة البيانات واحفظها
4. انتظر حتى يجهز المشروع

## 🔑 الخطوة 2: احصل على رابط الاتصال (Connection String)

1. **Project Settings** → **Database**
2. ابحث عن قسم **Connection string** واختر تبويب **URI**
3. يفضَّل استخدام وضع **Transaction pooler** (المنفذ 6543) لأنه أنسب للتطبيقات المستضافة مثل Render
4. انسخ الرابط، شكله يكون تقريباً:
   ```
   postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-xxxxx.pooler.supabase.com:6543/postgres
   ```
5. استبدل `[YOUR-PASSWORD]` بكلمة المرور الحقيقية التي اخترتها في الخطوة 1

هذا الرابط الكامل هو قيمة متغير البيئة `DATABASE_URL`.

## 📤 الخطوة 3: ارفع الملفات على GitHub

بما أن كل الملفات الآن في مجلد واحد (لا مجلدات فرعية)، ارفعها بنفس الطريقة
التي استخدمتها مع بوت التصميم:

1. أنشئ مستودع جديد (Private يُفضّل، لأن فيه أرقام ADMIN الخاصة بك لاحقاً)
2. **uploading an existing file** → اختر الملفات **واحداً واحداً** (كما فعلت سابقاً) حتى تضيفها كلها:
   - `main.py`, `config.py`, `db_core.py`, `db_models.py`, `db_crud.py`
   - `kb_admin.py`, `kb_student.py`
   - `h_common.py`, `h_admin_panel.py`, `h_admin_add_content.py`, `h_admin_manage_content.py`, `h_admin_stats.py`, `h_admin_broadcast.py`
   - `h_student_start.py`, `h_student_study.py`, `h_student_quiz.py`, `h_student_ask_atlas.py`, `h_student_challenge.py`, `h_student_progress.py`, `h_student_search.py`, `h_student_misc.py`
   - `utils_decorators.py`, `utils_helpers.py`, `utils_forms.py`
   - `requirements.txt`, `render.yaml`, `README.md`, `.env.example`
3. **Commit changes**

## 🚀 الخطوة 4: انشر على Render

1. **New +** → **Blueprint** → اختر المستودع (سيقرأ `render.yaml` تلقائياً ويقترح **Worker**)
2. أضف متغيرات البيئة التالية من تبويب **Environment**:

| المتغير | القيمة |
|---|---|
| `BOT_TOKEN` | توكن هذا البوت من BotFather (مختلف عن توكن بوت التصميم) |
| `ADMIN_IDS` | رقمك التعريفي (يمكن أكثر من رقم مفصولين بفاصلة) |
| `DATABASE_URL` | الرابط الكامل من الخطوة 2 |
| `ANTHROPIC_API_KEY` | اختياري — اتركه فارغاً إذا لا تملك مفتاح Anthropic API |

3. **Save Changes** — سيبدأ النشر تلقائياً

## ⚠️ ملاحظة مهمة عن نوع الخدمة

هذا البوت أيضاً يعمل بنظام **Polling** (لا يفتح منفذ ويب)، لذا يجب أن يكون
نوع الخدمة على Render هو **Background Worker** — تماماً مثل بوت التصميم،
وليس Web Service. ملف `render.yaml` يحدد هذا تلقائياً بصيغة `type: worker`.

## 📝 ملاحظة عن حفظ حالة المحادثة

البوت يستخدم ملف `atlas2010_bot_state.pickle` لحفظ حالة المحادثات الجارية.
على Render (القرص غير دائم)، قد يُمسح هذا الملف عند إعادة تشغيل الخدمة —
هذا لا يؤثر على البيانات المحفوظة في قاعدة البيانات (تقدم الطلاب، النقاط،
المحتوى)، فقط قد يحتاج الطالب يعيد فتح القائمة إذا كان في منتصف خطوة عند
إعادة التشغيل.

## 🧩 هيكل الملفات الأصلي (للمرجعية فقط)

قبل التسطيح كانت الملفات منظمة هكذا؛ الوظيفة متطابقة تماماً في النسخة الحالية:

```
database/db.py       → db_core.py
database/models.py   → db_models.py
database/crud.py     → db_crud.py
keyboards/admin_kb.py    → kb_admin.py
keyboards/student_kb.py  → kb_student.py
handlers/common.py       → h_common.py
handlers/student/*.py    → h_student_*.py
handlers/admin/*.py      → h_admin_*.py
utils/*.py                → utils_*.py
```
