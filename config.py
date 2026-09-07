"""
إعدادات المشروع - يتم تحميلها من ملف .env
لا تضع أي أسرار حقيقية هنا، استخدم فقط متغيرات البيئة.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# توكن البوت من BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# قائمة Telegram IDs المسموح لها بالدخول للوحة الإدارة (مفصولة بفواصل)
ADMIN_IDS = [
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]

# رابط قاعدة البيانات (افتراضياً SQLite محلية - لا تحتاج أي تثبيت إضافي)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///atlas2010.db")

# مفتاح Anthropic API اختياري لتفعيل ذكاء "اسأل أطلس" الحقيقي
# إذا تُرك فارغاً، سيعمل القسم برسالة توضيحية بدل الشرح الآلي
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# هوية المشروع
BOT_DISPLAY_NAME = "🎓 أطلس 2010 | رياضيات 2 ثانوي"
BOT_SLOGAN = "«افهم. راجع. اختبر. تفوق.»"

# عدد العناصر في كل صفحة عند استخدام Pagination
PAGE_SIZE = 6

# قيم نقاط الخبرة (XP)
XP_LESSON_COMPLETE = 10
XP_QUIZ_TAKEN = 20
XP_CORRECT_ANSWER = 5
XP_DAILY_CHALLENGE = 30

if not BOT_TOKEN:
    print("⚠️  تحذير: لم يتم ضبط BOT_TOKEN في ملف .env")
if not ADMIN_IDS:
    print("⚠️  تحذير: لم يتم ضبط أي ADMIN_IDS في ملف .env - لن يستطيع أحد الدخول للوحة الإدارة")
