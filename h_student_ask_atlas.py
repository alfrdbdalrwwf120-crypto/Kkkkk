"""
قسم "اسأل أطلس": يستقبل من الطالب نصاً أو صورة لمسألة رياضية،
ويرد بشرح تدريجي للحل (وليس الإجابة النهائية فقط).

إذا تم ضبط ANTHROPIC_API_KEY في .env، يتم استخدام Claude فعلياً
(بما في ذلك الرؤية لقراءة صور المسائل). إن لم يُضبط، يظهر للطالب
تنبيه واضح بدل تعطّل البوت - لتبقى بقية الميزات تعمل دائماً.
"""
import base64

from telegram import Update
from telegram.ext import ContextTypes

from kb_student import back_home_kb, cancel_kb
from utils_helpers import safe_edit
from config import ANTHROPIC_API_KEY

ASK_ATLAS_STATE = "ask_atlas"

SYSTEM_PROMPT = (
    "أنت 'أطلس'، مساعد تعليمي متخصص في مادة الرياضيات لطلبة السنة الثانية ثانوي في ليبيا. "
    "مهمتك مساعدة الطالب على فهم حل المسألة خطوة بخطوة، بأسلوب مبسط وواضح باللغة العربية. "
    "لا تعطِ الإجابة النهائية مباشرة أولاً، بل اشرح الخطوات المنطقية للوصول للحل، "
    "ثم اذكر الناتج النهائي في الخطوة الأخيرة. إن كانت المسألة أو الصورة غير واضحة، "
    "اطلب من الطالب إعادة إرسالها بوضوح أكبر."
)


async def prompt_ask_atlas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting"] = ASK_ATLAS_STATE
    text = (
        "🧠 اسأل أطلس\n\n"
        "أرسل لي المسألة التي تريد فهم حلّها:\n"
        "✍️ اكتبها نصاً، أو\n"
        "📷 أرسل صورة واضحة لها."
    )
    await safe_edit(query, text, reply_markup=cancel_kb("home"))


async def handle_ask_atlas_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    await _respond(update, context, text_question=question)


async def handle_ask_atlas_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    tg_file = await photo.get_file()
    photo_bytes = await tg_file.download_as_bytearray()
    await _respond(update, context, image_bytes=bytes(photo_bytes))


async def _respond(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    text_question: str | None = None, image_bytes: bytes | None = None):
    context.user_data.pop("awaiting", None)
    thinking_msg = await update.message.reply_text("🧠 أطلس يفكر في المسألة...")

    if not ANTHROPIC_API_KEY:
        await thinking_msg.edit_text(
            "⚠️ ميزة الشرح الآلي غير مفعّلة حالياً من قِبل الإدارة.\n"
            "يمكنك استخدام قسم 📚 ابدأ الدراسة أو 🔍 البحث لمراجعة الدرس المرتبط بهذه المسألة.",
        )
        await update.message.reply_text("القائمة الرئيسية 👇", reply_markup=back_home_kb())
        return

    try:
        answer = await _ask_claude(text_question=text_question, image_bytes=image_bytes)
        await thinking_msg.edit_text(answer)
    except Exception as e:
        await thinking_msg.edit_text(
            "⚠️ تعذّر معالجة سؤالك حالياً. تأكد أن الصورة واضحة أو حاول كتابة المسألة نصاً."
        )
    await update.message.reply_text("القائمة الرئيسية 👇", reply_markup=back_home_kb())


async def _ask_claude(text_question: str | None, image_bytes: bytes | None) -> str:
    """يستدعي Anthropic API لتوليد شرح تدريجي. يعمل بشكل متزامن داخل executor
    لأن مكتبة anthropic الرسمية تعمل بشكل sync افتراضياً."""
    import asyncio
    import anthropic

    def _call():
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        content = []
        if image_bytes is not None:
            b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
            })
            content.append({"type": "text", "text": "اشرح لي حل هذه المسألة خطوة بخطوة."})
        else:
            content.append({"type": "text", "text": text_question or ""})

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
        return "".join(block.text for block in message.content if block.type == "text")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _call)
