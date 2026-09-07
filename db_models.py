"""
نماذج قاعدة البيانات (SQLAlchemy ORM)
هذا الملف هو "المصدر الواحد للحقيقة" لهيكل البيانات.
إضافة وحدة/درس/فيديو/اختبار جديد لا يتطلب أبداً تعديل هذا الملف أو أي كود آخر -
فقط يُضاف كصف (row) جديد في الجداول أدناه عبر لوحة الإدارة.
"""
from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, DateTime, Date,
    ForeignKey
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    username = Column(String(255), nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)

    xp = Column(Integer, default=0)
    level_code = Column(String(50), default="مبتدئ")
    streak_days = Column(Integer, default=0)
    last_active_date = Column(Date, nullable=True)

    last_lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    notifications_enabled = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)

    progress_items = relationship("Progress", back_populates="user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    order = Column(Integer, default=0)
    image_file_id = Column(String(255), nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    lessons = relationship(
        "Lesson", back_populates="unit", order_by="Lesson.order",
        cascade="all, delete-orphan"
    )
    files = relationship("FileItem", back_populates="unit")
    quizzes = relationship("Quiz", back_populates="unit")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    content_text = Column(Text, default="")  # الشرح المكتوب
    examples_text = Column(Text, default="")  # الأمثلة المحلولة
    exercises_text = Column(Text, default="")  # التمارين
    order = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    unit = relationship("Unit", back_populates="lessons")
    videos = relationship("Video", back_populates="lesson", order_by="Video.order")
    files = relationship("FileItem", back_populates="lesson")
    quizzes = relationship("Quiz", back_populates="lesson")
    questions = relationship("Question", back_populates="lesson")
    progress_items = relationship("Progress", back_populates="lesson")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    file_id = Column(String(255), nullable=True)   # Telegram file_id
    url = Column(String(500), nullable=True)        # أو رابط خارجي
    thumbnail_file_id = Column(String(255), nullable=True)
    order = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)

    lesson = relationship("Lesson", back_populates="videos")


class FileItem(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    name = Column(String(255), nullable=False)
    file_id = Column(String(255), nullable=False)  # Telegram file_id
    description = Column(Text, default="")
    file_type = Column(String(50), default="pdf")  # pdf/summary/worksheet/exercises/review/exam
    is_published = Column(Boolean, default=True)

    unit = relationship("Unit", back_populates="files")
    lesson = relationship("Lesson", back_populates="files")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    quiz_type = Column(String(50), default="lesson")  # quick/lesson/unit/comprehensive
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    duration_minutes = Column(Integer, default=0)  # 0 = بلا وقت محدد
    pass_score = Column(Integer, default=50)  # نسبة النجاح %
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    unit = relationship("Unit", back_populates="quizzes")
    lesson = relationship("Lesson", back_populates="quizzes")
    questions = relationship(
        "Question", back_populates="quiz", order_by="Question.order",
        cascade="all, delete-orphan"
    )
    attempts = relationship("QuizAttempt", back_populates="quiz")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)

    text = Column(Text, nullable=False)
    image_file_id = Column(String(255), nullable=True)
    option_a = Column(String(500), nullable=False)
    option_b = Column(String(500), nullable=False)
    option_c = Column(String(500), nullable=False)
    option_d = Column(String(500), nullable=False)
    correct_option = Column(String(1), nullable=False)  # A/B/C/D
    explanation = Column(Text, default="")
    points = Column(Integer, default=1)
    order = Column(Integer, default=0)

    quiz = relationship("Quiz", back_populates="questions")
    lesson = relationship("Lesson", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    percentage = Column(Integer, default=0)
    passed = Column(Boolean, default=False)
    taken_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")
    answers = relationship(
        "AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_option = Column(String(1), nullable=True)
    is_correct = Column(Boolean, default=False)

    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question")


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    status = Column(String(20), default="in_progress")  # in_progress/completed
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="progress_items")
    lesson = relationship("Lesson", back_populates="progress_items")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    icon = Column(String(10), default="🏆")
    requirement_type = Column(String(30), default="xp")  # xp/lessons/quizzes/streak
    requirement_value = Column(Integer, default=0)

    user_links = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_links")


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    ann_type = Column(String(30), default="general")  # general/new_lesson/new_quiz/new_file/alert
    content = Column(Text, nullable=False)
    image_file_id = Column(String(255), nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    sent_by = Column(BigInteger, nullable=True)


class DailyChallenge(Base):
    __tablename__ = "daily_challenges"

    id = Column(Integer, primary_key=True)
    challenge_date = Column(Date, default=date.today)
    question_text = Column(Text, nullable=False)
    image_file_id = Column(String(255), nullable=True)
    option_a = Column(String(500), nullable=False)
    option_b = Column(String(500), nullable=False)
    option_c = Column(String(500), nullable=False)
    option_d = Column(String(500), nullable=False)
    correct_option = Column(String(1), nullable=False)
    explanation = Column(Text, default="")
    is_active = Column(Boolean, default=True)

    attempts = relationship("DailyChallengeAttempt", back_populates="challenge")


class DailyChallengeAttempt(Base):
    __tablename__ = "daily_challenge_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("daily_challenges.id"), nullable=False)
    selected_option = Column(String(1), nullable=True)
    is_correct = Column(Boolean, default=False)
    answered_at = Column(DateTime, default=datetime.utcnow)

    challenge = relationship("DailyChallenge", back_populates="attempts")


class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)
