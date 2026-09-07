"""
دوال مساعدة للتعامل مع قاعدة البيانات (CRUD) ومنطق الأعمال المشترك
(نقاط الخبرة، التقدم، الإنجازات...). كل الـ handlers تستخدم هذا الملف
بدلاً من كتابة استعلامات SQLAlchemy مباشرة، لتسهيل الصيانة.
"""
from datetime import datetime, date, timedelta

from sqlalchemy import or_

from db_models import (
    User, Unit, Lesson, Video, FileItem, Quiz, Question, QuizAttempt,
    AttemptAnswer, Progress, Achievement, UserAchievement, Announcement,
    DailyChallenge, DailyChallengeAttempt, AdminLog,
)
from config import XP_LESSON_COMPLETE, XP_QUIZ_TAKEN, XP_CORRECT_ANSWER, XP_DAILY_CHALLENGE


# ------------------------------------------------------------------ #
# المستخدمون
# ------------------------------------------------------------------ #
def get_or_create_user(session, telegram_user) -> User:
    user = session.query(User).filter_by(telegram_id=telegram_user.id).first()
    if user:
        # تحديث الاسم/المعرف إن تغيّر + تحديث آخر نشاط والـ streak
        user.full_name = telegram_user.full_name
        user.username = telegram_user.username
        update_streak(session, user)
        session.commit()
        return user

    user = User(
        telegram_id=telegram_user.id,
        full_name=telegram_user.full_name,
        username=telegram_user.username,
        registered_at=datetime.utcnow(),
        last_active_date=date.today(),
        streak_days=1,
    )
    session.add(user)
    session.commit()
    return user


def update_streak(session, user: User):
    today = date.today()
    if user.last_active_date == today:
        return
    if user.last_active_date == today - timedelta(days=1):
        user.streak_days = (user.streak_days or 0) + 1
    else:
        user.streak_days = 1
    user.last_active_date = today


def get_user_by_tid(session, telegram_id: int) -> User | None:
    return session.query(User).filter_by(telegram_id=telegram_id).first()


# ------------------------------------------------------------------ #
# نقاط الخبرة (XP) والمستويات والإنجازات
# ------------------------------------------------------------------ #
LEVELS = [
    (0, "🌱 مبتدئ"),
    (100, "📘 مجتهد"),
    (300, "🥇 متفوق"),
    (700, "💎 متميز"),
    (1500, "👑 أسطورة أطلس"),
]


def _compute_level(xp: int) -> str:
    level = LEVELS[0][1]
    for threshold, name in LEVELS:
        if xp >= threshold:
            level = name
    return level


def add_xp(session, user: User, amount: int) -> list[Achievement]:
    """يضيف XP للمستخدم، يحدث مستواه، ويرجع أي إنجازات جديدة تم فتحها."""
    user.xp = (user.xp or 0) + amount
    user.level_code = _compute_level(user.xp)

    newly_unlocked = []
    earned_ids = {
        ua.achievement_id
        for ua in session.query(UserAchievement).filter_by(user_id=user.id).all()
    }
    achievements = session.query(Achievement).filter_by(requirement_type="xp").all()
    for ach in achievements:
        if ach.id not in earned_ids and user.xp >= ach.requirement_value:
            session.add(UserAchievement(user_id=user.id, achievement_id=ach.id))
            newly_unlocked.append(ach)

    session.commit()
    return newly_unlocked


# ------------------------------------------------------------------ #
# الوحدات والدروس
# ------------------------------------------------------------------ #
def get_published_units(session):
    return (
        session.query(Unit)
        .filter_by(is_published=True)
        .order_by(Unit.order)
        .all()
    )


def get_all_units(session):
    return session.query(Unit).order_by(Unit.order).all()


def get_unit(session, unit_id: int) -> Unit | None:
    return session.query(Unit).get(unit_id)


def get_published_lessons(session, unit_id: int):
    return (
        session.query(Lesson)
        .filter_by(unit_id=unit_id, is_published=True)
        .order_by(Lesson.order)
        .all()
    )


def get_lesson(session, lesson_id: int) -> Lesson | None:
    return session.query(Lesson).get(lesson_id)


def get_unit_progress_percent(session, user: User, unit: Unit) -> int:
    lessons = get_published_lessons(session, unit.id)
    if not lessons:
        return 0
    completed = (
        session.query(Progress)
        .filter(
            Progress.user_id == user.id,
            Progress.status == "completed",
            Progress.lesson_id.in_([l.id for l in lessons]),
        )
        .count()
    )
    return int(completed / len(lessons) * 100)


def get_lesson_status(session, user: User, lesson: Lesson) -> str:
    """يرجع: completed / in_progress / locked(غير مستخدم حالياً) بحسب تقدم الطالب."""
    prog = (
        session.query(Progress)
        .filter_by(user_id=user.id, lesson_id=lesson.id)
        .first()
    )
    if prog and prog.status == "completed":
        return "completed"
    return "available"


def mark_lesson_complete(session, user: User, lesson: Lesson):
    prog = (
        session.query(Progress)
        .filter_by(user_id=user.id, lesson_id=lesson.id)
        .first()
    )
    already_completed = prog and prog.status == "completed"
    if not prog:
        prog = Progress(user_id=user.id, lesson_id=lesson.id)
        session.add(prog)
    prog.status = "completed"
    prog.completed_at = datetime.utcnow()
    user.last_lesson_id = lesson.id
    session.commit()

    if not already_completed:
        return add_xp(session, user, XP_LESSON_COMPLETE)
    return []


def touch_last_lesson(session, user: User, lesson: Lesson):
    user.last_lesson_id = lesson.id
    session.commit()


# ------------------------------------------------------------------ #
# الفيديوهات والملفات
# ------------------------------------------------------------------ #
def get_lesson_videos(session, lesson_id: int):
    return (
        session.query(Video)
        .filter_by(lesson_id=lesson_id, is_published=True)
        .order_by(Video.order)
        .all()
    )


def get_lesson_files(session, lesson_id: int):
    return session.query(FileItem).filter_by(lesson_id=lesson_id, is_published=True).all()


# ------------------------------------------------------------------ #
# الاختبارات
# ------------------------------------------------------------------ #
def get_quiz(session, quiz_id: int) -> Quiz | None:
    return session.query(Quiz).get(quiz_id)


def get_lesson_quizzes(session, lesson_id: int):
    return session.query(Quiz).filter_by(lesson_id=lesson_id, is_published=True).all()


def get_unit_quiz(session, unit_id: int):
    return (
        session.query(Quiz)
        .filter_by(unit_id=unit_id, quiz_type="unit", is_published=True)
        .first()
    )


def get_quiz_questions(session, quiz_id: int):
    return (
        session.query(Question)
        .filter_by(quiz_id=quiz_id)
        .order_by(Question.order)
        .all()
    )


def save_quiz_attempt(session, user: User, quiz: Quiz, answers: dict) -> QuizAttempt:
    """answers: {question_id: selected_option}"""
    questions = get_quiz_questions(session, quiz.id)
    score = 0
    total = sum(q.points for q in questions) or len(questions)

    attempt = QuizAttempt(user_id=user.id, quiz_id=quiz.id, total=total)
    session.add(attempt)
    session.flush()

    correct_count = 0
    for q in questions:
        selected = answers.get(q.id)
        is_correct = bool(selected) and selected == q.correct_option
        if is_correct:
            score += q.points
            correct_count += 1
        session.add(
            AttemptAnswer(
                attempt_id=attempt.id,
                question_id=q.id,
                selected_option=selected,
                is_correct=is_correct,
            )
        )

    percentage = int(score / total * 100) if total else 0
    attempt.score = score
    attempt.percentage = percentage
    attempt.passed = percentage >= quiz.pass_score
    session.commit()

    add_xp(session, user, XP_QUIZ_TAKEN + correct_count * XP_CORRECT_ANSWER)
    return attempt


def get_user_quiz_attempts_count(session, user_id: int) -> int:
    return session.query(QuizAttempt).filter_by(user_id=user_id).count()


def get_user_average_score(session, user_id: int) -> int:
    attempts = session.query(QuizAttempt).filter_by(user_id=user_id).all()
    if not attempts:
        return 0
    return int(sum(a.percentage for a in attempts) / len(attempts))


# ------------------------------------------------------------------ #
# تحدي اليوم
# ------------------------------------------------------------------ #
def get_active_daily_challenge(session) -> DailyChallenge | None:
    return (
        session.query(DailyChallenge)
        .filter_by(is_active=True)
        .order_by(DailyChallenge.id.desc())
        .first()
    )


def has_answered_challenge(session, user_id: int, challenge_id: int) -> bool:
    return (
        session.query(DailyChallengeAttempt)
        .filter_by(user_id=user_id, challenge_id=challenge_id)
        .first()
        is not None
    )


def answer_daily_challenge(session, user: User, challenge: DailyChallenge, option: str):
    is_correct = option == challenge.correct_option
    session.add(
        DailyChallengeAttempt(
            user_id=user.id,
            challenge_id=challenge.id,
            selected_option=option,
            is_correct=is_correct,
        )
    )
    session.commit()
    if is_correct:
        add_xp(session, user, XP_DAILY_CHALLENGE)
    return is_correct


# ------------------------------------------------------------------ #
# الإنجازات
# ------------------------------------------------------------------ #
def get_all_achievements(session):
    return session.query(Achievement).order_by(Achievement.requirement_value).all()


def get_user_achievement_ids(session, user_id: int) -> set:
    return {
        ua.achievement_id
        for ua in session.query(UserAchievement).filter_by(user_id=user_id).all()
    }


# ------------------------------------------------------------------ #
# البحث
# ------------------------------------------------------------------ #
def search_content(session, term: str):
    like = f"%{term}%"
    results = {
        "units": session.query(Unit).filter(Unit.name.ilike(like), Unit.is_published == True).all(),
        "lessons": session.query(Lesson).filter(Lesson.name.ilike(like), Lesson.is_published == True).all(),
        "videos": session.query(Video).filter(Video.name.ilike(like), Video.is_published == True).all(),
        "files": session.query(FileItem).filter(FileItem.name.ilike(like), FileItem.is_published == True).all(),
        "quizzes": session.query(Quiz).filter(Quiz.name.ilike(like), Quiz.is_published == True).all(),
    }
    return results


# ------------------------------------------------------------------ #
# الإعلانات
# ------------------------------------------------------------------ #
def create_announcement(session, ann_type: str, content: str, sent_by: int, image_file_id=None) -> Announcement:
    ann = Announcement(ann_type=ann_type, content=content, sent_by=sent_by, image_file_id=image_file_id)
    session.add(ann)
    session.commit()
    return ann


def get_recent_announcements(session, limit=10):
    return session.query(Announcement).order_by(Announcement.sent_at.desc()).limit(limit).all()


def get_all_students(session):
    return session.query(User).order_by(User.xp.desc()).all()


def get_leaderboard(session, limit=10):
    return session.query(User).order_by(User.xp.desc()).limit(limit).all()


# ------------------------------------------------------------------ #
# سجلات الإدارة
# ------------------------------------------------------------------ #
def log_admin_action(session, admin_id: int, action: str, details: str = ""):
    session.add(AdminLog(admin_id=admin_id, action=action, details=details))
    session.commit()


# ------------------------------------------------------------------ #
# إحصائيات عامة
# ------------------------------------------------------------------ #
def get_global_stats(session):
    return {
        "students": session.query(User).count(),
        "active_students": session.query(User)
            .filter(User.last_active_date >= date.today() - timedelta(days=7))
            .count(),
        "units": session.query(Unit).count(),
        "lessons": session.query(Lesson).count(),
        "videos": session.query(Video).count(),
        "files": session.query(FileItem).count(),
        "quizzes": session.query(Quiz).count(),
        "questions": session.query(Question).count(),
    }
