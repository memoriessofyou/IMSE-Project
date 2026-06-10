from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import pymysql
import os

router = APIRouter()

def get_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "apppassword"),
        database=os.getenv("DB_NAME", "language_app"),
        cursorclass=pymysql.cursors.DictCursor
    )

class ReviewStartRequest(BaseModel):
    user_id: int

class ReviewSubmitRequest(BaseModel):
    user_id: int
    word_id: int
    session_id: int
    is_correct: bool

@router.post("/api/review/start")
def start_review_session(request: ReviewStartRequest):
    db = get_db()
    try:
        with db.cursor() as cursor:
            # Check if user exists
            cursor.execute("SELECT * FROM Users WHERE user_id = %s", (request.user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")
            
            # Check if user has words assigned and pending review
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM User_Words 
                WHERE user_id = %s AND (next_review IS NULL OR next_review <= NOW())
            """, (request.user_id,))
            res = cursor.fetchone()
            if res['count'] == 0:
                return {"message": "No words for today! Come back tomorrow :)"}

            # Create learning session
            cursor.execute(
                "INSERT INTO Learning_Sessions (user_id, session_type, start_time, words_count) VALUES (%s, %s, %s, %s)",
                (request.user_id, "Word Review", datetime.now(), 0)
            )
            session_id = cursor.lastrowid
            db.commit()
            return {"session_id": session_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/api/review/next-word")
def get_next_word(user_id: int):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT w.word_id, w.word, w.translation, uw.is_new, uw.problematic, uw.interval
                FROM User_Words uw
                JOIN Words w ON w.word_id = uw.word_id
                WHERE uw.user_id = %s AND (uw.next_review IS NULL OR uw.next_review <= NOW())
                ORDER BY uw.next_review ASC
                LIMIT 1
            """, (user_id,))
            word = cursor.fetchone()
            if not word:
                return {"message": "No more words to review", "finished": True}
            return {**word, "finished": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/api/review/submit")
def submit_review_result(request: ReviewSubmitRequest):
    db = get_db()
    try:
        with db.cursor() as cursor:
            # Get current word status
            cursor.execute(
                "SELECT * FROM User_Words WHERE user_id = %s AND word_id = %s",
                (request.user_id, request.word_id)
            )
            uw = cursor.fetchone()
            if not uw:
                raise HTTPException(status_code=404, detail="User-Word relationship not found")

            # Spaced repetition logic
            current_interval = uw['interval'] or 0
            if request.is_correct:
                new_interval = max(1, current_interval * 2) if current_interval > 0 else 1
                problematic = 0
                last_mistake = uw['last_mistake']
            else:
                new_interval = 1
                problematic = 1
                last_mistake = datetime.now()

            next_review_date = datetime.now() + timedelta(days=new_interval)

            # Update User_Words
            cursor.execute("""
                UPDATE User_Words 
                SET problematic = %s, 
                    last_mistake = %s, 
                    `interval` = %s, 
                    next_review = %s, 
                    last_reviewed = %s,
                    is_new = 0,
                    correct_count = correct_count + %s,
                    mistakes_count = mistakes_count + %s
                WHERE user_id = %s AND word_id = %s
            """, (
                problematic, 
                last_mistake, 
                new_interval, 
                next_review_date, 
                datetime.now(),
                1 if request.is_correct else 0,
                0 if request.is_correct else 1,
                request.user_id, 
                request.word_id
            ))

            # Update Word table (as per prompt: "correct_count, mistake_count in Word table are incremented")
            # First check if columns exist in Words table to avoid errors if they are not yet added
            cursor.execute("SHOW COLUMNS FROM Words LIKE 'correct_count'")
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE Words 
                    SET correct_count = correct_count + %s, 
                        mistake_count = mistake_count + %s
                    WHERE word_id = %s
                """, (
                    1 if request.is_correct else 0,
                    0 if request.is_correct else 1,
                    request.word_id
                ))

            # Update learning_session
            cursor.execute("""
                UPDATE Learning_Sessions 
                SET words_count = words_count + 1 
                WHERE session_id = %s
            """, (request.session_id,))

            db.commit()
            return {"status": "success", "next_review": next_review_date}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/api/review/analytics")
def get_review_analytics(user_id: int):
    db = get_db()
    try:
        with db.cursor() as cursor:
            # Get stats for the user
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_assigned,
                    SUM(CASE WHEN is_new = 0 THEN 1 ELSE 0 END) as reviewed_at_least_once,
                    SUM(problematic) as problematic_words,
                    AVG(correct_count / (correct_count + mistakes_count + 0.0001)) * 100 as accuracy
                FROM User_Words 
                WHERE user_id = %s
            """, (user_id,))
            stats = cursor.fetchone()
            
            # Get recent sessions
            cursor.execute("""
                SELECT words_count, start_time, end_time 
                FROM Learning_Sessions 
                WHERE user_id = %s AND session_type = 'Word Review'
                ORDER BY start_time DESC LIMIT 5
            """, (user_id,))
            sessions = cursor.fetchall()
            
            return {
                "stats": stats,
                "recent_sessions": sessions
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/api/review/session-report")
def get_session_report(user_id: int):
    db = get_db()
    try:
        with db.cursor() as cursor:
            # This query follows the logic provided by the user to get detailed word-level progress
            # from the most recent learning session.
            sql = """
                SELECT 
                    u.username,
                    w.word,
                    t.name AS topic_name,
                    uw.correct_count,
                    uw.mistakes_count,
                    uw.next_review,
                    ls.session_type,
                    ls.words_count AS last_session_volume
                FROM Users u
                JOIN User_Words uw ON u.user_id = uw.user_id
                JOIN Words w ON uw.word_id = w.word_id
                JOIN Wordlist_Words ww ON w.word_id = ww.word_id
                JOIN Wordlists wl ON ww.wordlist_id = wl.wordlist_id
                JOIN Topics t ON wl.topic_id = t.topic_id
                JOIN Learning_Sessions ls ON u.user_id = ls.user_id 
                    AND DATE(uw.last_reviewed) = DATE(ls.start_time)
                WHERE u.user_id = %s
                  AND ls.session_id = (SELECT MAX(session_id) FROM Learning_Sessions WHERE user_id = u.user_id)
                ORDER BY t.name, uw.next_review
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/api/review/end")
def end_review_session(session_id: int):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE Learning_Sessions SET end_time = NOW() WHERE session_id = %s",
                (session_id,)
            )
            db.commit()
            return {"status": "session ended"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
