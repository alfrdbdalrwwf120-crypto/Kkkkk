"""
تهيئة الاتصال بقاعدة البيانات وإنشاء الجداول.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from config import DATABASE_URL
from db_models import Base, Achievement

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

DEFAULT_ACHIEVEMENTS = [
    dict(code="beginner", name="🌱 مبتدئ", description="مرحباً بك في رحلتك مع أطلس",
         icon="🌱", requirement_type="xp", requirement_value=0),
    dict(code="diligent", name="📘 مجتهد", description="وصلت إلى 100 نقطة خبرة",
         icon="📘", requirement_type="xp", requirement_value=100),
    dict(code="excellent", name="🥇 متفوق", description="وصلت إلى 300 نقطة خبرة",
         icon="🥇", requirement_type="xp", requirement_value=300),
    dict(code="outstanding", name="💎 متميز", description="وصلت إلى 700 نقطة خبرة",
         icon="💎", requirement_type="xp", requirement_value=700),
    dict(code="legend", name="👑 أسطورة أطلس", description="وصلت إلى 1500 نقطة خبرة",
         icon="👑", requirement_type="xp", requirement_value=1500),
]


def init_db():
    """إنشاء كل الجداول (إن لم تكن موجودة) وزرع الإنجازات الافتراضية."""
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        existing_codes = {a.code for a in session.query(Achievement).all()}
        for ach in DEFAULT_ACHIEVEMENTS:
            if ach["code"] not in existing_codes:
                session.add(Achievement(**ach))
        session.commit()
    finally:
        session.close()


def get_session():
    """إرجاع جلسة قاعدة بيانات جديدة. يجب إغلاقها بعد الاستخدام."""
    return SessionLocal()
