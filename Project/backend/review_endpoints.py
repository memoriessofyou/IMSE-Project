from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import pymysql
import os
from pymongo import MongoClient

router = APIRouter()
#Anna's use case
def get_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "apppassword"),
        database=os.getenv("DB_NAME", "language_app"),
        cursorclass=pymysql.cursors.DictCursor
    )

def get_mongo():
    client = MongoClient(
        host=os.getenv("MONGO_HOST", "mongodb"),
        port=int(os.getenv("MONGO_PORT", 27017))
    )
    return client["language_app"]

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
            cursor.execute("SELECT * FROM Users WHERE user_id = %s", (request.user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")

            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM User_Words 
                WHERE user_id = %s AND (next_review IS NULL OR next_review <= NOW())
            """, (request.user_id,))
            res = cursor.fetchone()
            if res['count'] == 0:
                return {"message": "No words for today! Come back tomorrow :)"}

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

            cursor.execute(
                "SELECT * FROM User_Words WHERE user_id = %s AND word_id = %s",
                (request.user_id, request.word_id)
            )
            uw = cursor.fetchone()
            if not uw:
                raise HTTPException(status_code=404, detail="User-Word relationship not found")

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
@router.post("/api/mongo/review/start")
def mongo_start_review_session(request: ReviewStartRequest):
    mongo = get_mongo()
    try:
        user = mongo.users.find_one({"_id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        now_str = str(datetime.now())
        words_to_review = [
            w for w in user.get("words", [])
            if w.get("next_review") is None or w.get("next_review") <= now_str
        ]
        
        if not words_to_review:
            return {"message": "No words for today! Come back tomorrow :)"}

        max_session = mongo.sessions.find_one(sort=[("_id", -1)])
        session_id = (max_session["_id"] + 1) if max_session else 1

        mongo.sessions.insert_one({
            "_id": session_id,
            "user_id": request.user_id,
            "session_type": "Word Review",
            "start_time": str(datetime.now()),
            "end_time": None,
            "words_count": 0
        })

        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/mongo/review/next-word")
def mongo_get_next_word(user_id: int):
    mongo = get_mongo()
    try:
        user = mongo.users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        now_str = str(datetime.now())
        words_to_review = [
            w for w in user.get("words", [])
            if w.get("next_review") is None or w.get("next_review") <= now_str
        ]

        if not words_to_review:
            return {"message": "No more words to review", "finished": True}

        def get_sort_key(w):
            val = w.get("next_review")
            return val if val else ""
            
        words_to_review.sort(key=get_sort_key)
        word = words_to_review[0]

        return {
            "word_id": word["word_id"],
            "word": word.get("word"),
            "translation": word.get("translation"),
            "is_new": word.get("is_new"),
            "problematic": word.get("problematic"),
            "interval": word.get("interval"),
            "finished": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/mongo/review/submit")
def mongo_submit_review_result(request: ReviewSubmitRequest):
    mongo = get_mongo()
    try:
        user = mongo.users.find_one({"_id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        word_data = next((w for w in user.get("words", []) if w["word_id"] == request.word_id), None)
        if not word_data:
            raise HTTPException(status_code=404, detail="User-Word relationship not found")

        current_interval = word_data.get('interval') or 0
        now = datetime.now()
        
        if request.is_correct:
            new_interval = max(1, current_interval * 2) if current_interval > 0 else 1
            problematic = False
            last_mistake = word_data.get('last_mistake')
        else:
            new_interval = 1
            problematic = True
            last_mistake = str(now)

        next_review_date = str(now + timedelta(days=new_interval))

        mongo.users.update_one(
            {"_id": request.user_id, "words.word_id": request.word_id},
            {
                "$set": {
                    "words.$.problematic": problematic,
                    "words.$.last_mistake": last_mistake,
                    "words.$.interval": new_interval,
                    "words.$.next_review": next_review_date,
                    "words.$.last_reviewed": str(now),
                    "words.$.is_new": False
                },
                "$inc": {
                    "words.$.correct_count": 1 if request.is_correct else 0,
                    "words.$.mistakes_count": 0 if request.is_correct else 1
                }
            }
        )

        mongo.words.update_one(
            {"_id": request.word_id},
            {
                "$inc": {
                    "correct_count": 1 if request.is_correct else 0,
                    "mistake_count": 0 if request.is_correct else 1
                }
            }
        )

        mongo.sessions.update_one(
            {"_id": request.session_id},
            {"$inc": {"words_count": 1}}
        )

        return {"status": "success", "next_review": next_review_date}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/mongo/review/analytics")
def mongo_get_review_analytics(user_id: int):
    mongo = get_mongo()
    try:
        user = mongo.users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        words = user.get("words", [])
        total_assigned = len(words)
        reviewed_at_least_once = sum(1 for w in words if not w.get("is_new"))
        problematic_words = sum(1 for w in words if w.get("problematic"))
        
        total_acc = 0
        for w in words:
            c = w.get("correct_count", 0)
            m = w.get("mistakes_count", 0)
            total_acc += (c / (c + m + 0.0001)) * 100
        
        accuracy = total_acc / total_assigned if total_assigned > 0 else 0
        
        stats = {
            "total_assigned": total_assigned,
            "reviewed_at_least_once": reviewed_at_least_once,
            "problematic_words": problematic_words,
            "accuracy": accuracy
        }

        sessions_cursor = mongo.sessions.find(
            {"user_id": user_id, "session_type": "Word Review"}
        ).sort("start_time", -1).limit(5)
        
        sessions = []
        for s in sessions_cursor:
            s["session_id"] = s.pop("_id")
            sessions.append(s)

        return {
            "stats": stats,
            "recent_sessions": sessions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/mongo/review/session-report")
def mongo_get_session_report(user_id: int):
    mongo = get_mongo()
    try:
        user = mongo.users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        latest_session = mongo.sessions.find_one(
            {"user_id": user_id},
            sort=[("_id", -1)]
        )
        if not latest_session or not latest_session.get("start_time"):
            return []

        session_date_str = latest_session["start_time"][:10]
        
        words = user.get("words", [])
        report = []
        for w in words:
            last_rev = w.get("last_reviewed")
            if last_rev and last_rev[:10] == session_date_str:
                wordlist = mongo.wordlists.find_one({"words": w["word_id"]})
                topic_name = wordlist.get("topic_name", "Unknown") if wordlist else "Unknown"

                report.append({
                    "username": user.get("username"),
                    "word": w.get("word"),
                    "topic_name": topic_name,
                    "correct_count": w.get("correct_count", 0),
                    "mistakes_count": w.get("mistakes_count", 0),
                    "next_review": w.get("next_review"),
                    "session_type": latest_session.get("session_type"),
                    "last_session_volume": latest_session.get("words_count", 0)
                })

        report.sort(key=lambda x: (x["topic_name"], x["next_review"] or ""))
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/mongo/review/end")
def mongo_end_review_session(session_id: int):
    mongo = get_mongo()
    try:
        mongo.sessions.update_one(
            {"_id": session_id},
            {"$set": {"end_time": str(datetime.now())}}
        )
        return {"status": "session ended"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
