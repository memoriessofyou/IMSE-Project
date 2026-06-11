# API for the project

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
import random
from datetime import datetime, timedelta
from pydantic import BaseModel
from pymongo import MongoClient
import os

load_dotenv()

from review_endpoints import router as review_router

app = FastAPI(
    title="Norwegian Learning App",
    description="Group Project for the course IMSE"
)

app.include_router(review_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



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



@app.post("/api/migrate")
def migrate_to_mongodb():
    db = get_db()
    mongo = get_mongo()
    try:
        mongo.users.drop()
        mongo.words.drop()
        mongo.wordlists.drop()
        mongo.topics.drop()
        mongo.sessions.drop()

        with db.cursor() as cursor:

            cursor.execute("SELECT * FROM Topics")
            topics = cursor.fetchall()
            if topics:
                mongo.topics.insert_many([
                    {
                        "_id": t["topic_id"],
                        "name": t["name"],
                        "description": t["description"]
                    }
                    for t in topics
                ])

            cursor.execute("SELECT * FROM Words")
            words = cursor.fetchall()
            if words:
                mongo.words.insert_many([
                    {
                        "_id": w["word_id"],
                        "word": w["word"],
                        "translation": w["translation"],
                        "difficulty_level": w["difficulty_level"],
                        "base_word_id": w["base_word_id"]
                    }
                    for w in words
                ])

            cursor.execute("""
                SELECT wl.*, t.name as topic_name
                FROM Wordlists wl
                JOIN Topics t ON wl.topic_id = t.topic_id
            """)
            wordlists = cursor.fetchall()
            for wl in wordlists:
                cursor.execute("""
                    SELECT word_id FROM Wordlist_Words
                    WHERE wordlist_id = %s
                """, (wl["wordlist_id"],))
                word_ids = [r["word_id"] for r in cursor.fetchall()]
                mongo.wordlists.insert_one({
                    "_id": wl["wordlist_id"],
                    "name": wl["name"],
                    "description": wl["description"],
                    "difficulty_level": wl["difficulty_level"],
                    "topic_id": wl["topic_id"],
                    "topic_name": wl["topic_name"],
                    "words": word_ids
                })

            cursor.execute("SELECT * FROM Users")
            users = cursor.fetchall()
            for user in users:
                uid = user["user_id"]
                cursor.execute("""
                    SELECT wordlist_id FROM User_Wordlists
                    WHERE user_id = %s
                """, (uid,))
                user_wordlist_ids = [r["wordlist_id"] for r in cursor.fetchall()]

                cursor.execute("""
                    SELECT uw.*, w.word, w.translation
                    FROM User_Words uw
                    JOIN Words w ON uw.word_id = w.word_id
                    WHERE uw.user_id = %s
                """, (uid,))
                user_words = cursor.fetchall()

                words_embedded = [
                    {
                        "word_id": uw["word_id"],
                        "word": uw["word"],
                        "translation": uw["translation"],
                        "is_new": bool(uw["is_new"]),
                        "problematic": bool(uw["problematic"]),
                        "correct_count": uw["correct_count"],
                        "mistakes_count": uw["mistakes_count"],
                        "interval": uw["interval"],
                        "next_review": str(uw["next_review"]) if uw["next_review"] else None,
                        "last_reviewed": str(uw["last_reviewed"]) if uw["last_reviewed"] else None,
                        "last_mistake": str(uw["last_mistake"]) if uw["last_mistake"] else None
                    }
                    for uw in user_words
                ]

                mongo.users.insert_one({
                    "_id": uid,
                    "username": user["username"],
                    "total_xp": user["total_xp"],
                    "wordlists": user_wordlist_ids,
                    "words": words_embedded
                })

            cursor.execute("SELECT * FROM Learning_Sessions")
            sessions = cursor.fetchall()
            if sessions:
                mongo.sessions.insert_many([
                    {
                        "_id": s["session_id"],
                        "user_id": s["user_id"],
                        "session_type": s["session_type"],
                        "start_time": str(s["start_time"]) if s["start_time"] else None,
                        "end_time": str(s["end_time"]) if s["end_time"] else None,
                        "words_count": s["words_count"]
                    }
                    for s in sessions
                ])

        return {"message": "Migration completed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/words")
def get_all_words():
    try:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM Words")
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/words/{id}")
def get_specific_word(id: int):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM Words WHERE word_id = %s", (id,))
            return cursor.fetchone()
    finally:
        db.close()



@app.get("/api/users")
def get_all_users():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT u.*,
                    CASE
                        WHEN a.user_id IS NOT NULL THEN 'Admin'
                        WHEN p.user_id IS NOT NULL THEN 'Premium'
                        WHEN b.user_id IS NOT NULL THEN 'Basic'
                        ELSE 'Unknown'
                    END AS user_type
                FROM Users u
                LEFT JOIN Admin_Users a ON u.user_id = a.user_id
                LEFT JOIN Premium_Users p ON u.user_id = p.user_id
                LEFT JOIN Basic_Users b ON u.user_id = b.user_id
            """)
            return cursor.fetchall()
    finally:
        db.close()

@app.get("/api/users/{id}")
def get_specific_user(id: int):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM Users WHERE user_id = %s", (id,))
            return cursor.fetchone()
    finally:
        db.close()



@app.get("/api/wordlist")
def get_all_wordlists():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM Wordlists")
            return cursor.fetchall()
    finally:
        db.close()

@app.get("/api/wordlist/{id}")
def get_specific_wordlist(id: int):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM Wordlists WHERE wordlist_id = %s", (id,))
            return cursor.fetchone()
    finally:
        db.close()

@app.get("/api/wordlist/{id}/words")
def get_wordlist_words(id: int):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM Wordlist_Words WHERE wordlist_id = %s", (id,)
            )
            return cursor.fetchall()
    finally:
        db.close()


@app.get("/api/topics")
def get_all_topics():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM Topics")
            return cursor.fetchall()
    finally:
        db.close()



@app.get("/api/users/{id}/words")
def get_words_from_user(id: int):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT w.word_id, w.word, w.translation, uw.is_new,
                       uw.correct_count, uw.mistakes_count, uw.next_review,
                       uw.last_reviewed, uw.problematic
                FROM User_Words uw
                JOIN Words w ON w.word_id = uw.word_id
                WHERE uw.user_id = %s
            """, (id,))
            return cursor.fetchall()
    finally:
        db.close()

@app.get("/api/users/{id}/wordlist")
def get_wordlist_from_user(id: int):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT wl.wordlist_id, wl.name
                FROM User_Wordlists uw
                JOIN Wordlists wl ON wl.wordlist_id = uw.wordlist_id
                WHERE uw.user_id = %s
            """, (id,))
            return cursor.fetchall()
    finally:
        db.close()



from db_generator import generate_data

from typing import Optional

@app.get("/api/admin/session-logs")
def get_session_logs(user_id: Optional[int] = None, date: Optional[str] = None):
    db = get_db()
    try:
        with db.cursor() as cursor:
            query = """
                SELECT
                    u.username,
                    DATE(ls.start_time) AS session_date,
                    t.name AS topic_name,
                    COUNT(DISTINCT w.word_id) AS words_practiced,
                    SUM(uw.correct_count) AS total_correct,
                    SUM(uw.mistakes_count) AS total_mistakes
                FROM Users u
                JOIN Learning_Sessions ls ON u.user_id = ls.user_id
                JOIN User_Words uw ON u.user_id = uw.user_id AND DATE(uw.last_reviewed) = DATE(ls.start_time)
                JOIN Words w ON uw.word_id = w.word_id
                JOIN Wordlist_Words ww ON w.word_id = ww.word_id
                JOIN Wordlists wl ON ww.wordlist_id = wl.wordlist_id
                JOIN Topics t ON wl.topic_id = t.topic_id
                WHERE 1=1
            """
            params = []
            if user_id:
                query += " AND u.user_id = %s "
                params.append(user_id)
            if date:
                query += " AND DATE(ls.start_time) = %s "
                params.append(date)
                
            query += """
                GROUP BY u.user_id, u.username, DATE(ls.start_time), t.topic_id, t.name
                ORDER BY session_date DESC, u.username ASC
                LIMIT 200
            """
            cursor.execute(query, tuple(params))
            
            # Format dates for JSON serialization
            results = cursor.fetchall()
            for row in results:
                if row['session_date']:
                    row['session_date'] = row['session_date'].strftime('%Y-%m-%d')
            return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/seed")
def seed_database():
    success = generate_data()
    if success:
        return {"message": "Database seeded successfully"}
    else:
        raise HTTPException(status_code=500, detail="Error seeding database")

# INES SQL Use Case


class AssignWordToWordListRequest(BaseModel):
    user_id: int
    word_id: int
    wordlist_id: int

@app.post("/api/assign-word-to-wordlist")
def assign_word_to_wordlist(request: AssignWordToWordListRequest):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM Users WHERE user_id = %s", (request.user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")

            cursor.execute("SELECT * FROM Words WHERE word_id = %s", (request.word_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Word not found")

            cursor.execute("SELECT * FROM Wordlists WHERE wordlist_id = %s", (request.wordlist_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Wordlist not found")

            cursor.execute("""
                UPDATE User_Words
                SET is_new = TRUE,
                    correct_count = 0,
                    `interval` = 0
                WHERE user_id = %s AND word_id = %s
            """, (request.user_id, request.word_id))

            cursor.execute("""
                INSERT IGNORE INTO Wordlist_Words (wordlist_id, word_id)
                VALUES (%s, %s)
            """, (request.wordlist_id, request.word_id))

            db.commit()
            return {"message": "Word re-assigned to wordlist successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# INES from SQL Analytics Report


@app.get("/api/analytics/difficult-words/{username}")
def get_difficult_words(username: str):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT
                    u.username,
                    w.word AS word_to_learn,
                    w.translation,
                    uw.correct_count AS progress,
                    uw.mistakes_count,
                    uw.next_review AS due_date,
                    wl.name AS wordlist_name,
                    uw.is_new
                FROM Users u
                JOIN User_Words uw ON u.user_id = uw.user_id
                JOIN Words w ON uw.word_id = w.word_id
                JOIN Wordlist_Words ww ON w.word_id = ww.word_id
                JOIN Wordlists wl ON ww.wordlist_id = wl.wordlist_id
                WHERE u.username = %s
                AND uw.is_new = TRUE
                ORDER BY uw.mistakes_count DESC
            """, (username,))
            return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# INES from MongoDB Use Case


@app.post("/api/mongo/assign-word-to-wordlist")
def mongo_assign_word_to_wordlist(request: AssignWordToWordListRequest):
    mongo = get_mongo()
    try:
        # check user exists
        user = mongo.users.find_one({"_id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # check word exists
        word = mongo.words.find_one({"_id": request.word_id})
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")

        # check wordlist exists
        wordlist = mongo.wordlists.find_one({"_id": request.wordlist_id})
        if not wordlist:
            raise HTTPException(status_code=404, detail="Wordlist not found")

        # reset word progress inside user document
        mongo.users.update_one(
            {
                "_id": request.user_id,
                "words.word_id": request.word_id
            },
            {
                "$set": {
                    "words.$.is_new": True,
                    "words.$.correct_count": 0,
                    "words.$.interval": 0
                }
            }
        )

        # re-link word to wordlist
        mongo.wordlists.update_one(
            {"_id": request.wordlist_id},
            {"$addToSet": {"words": request.word_id}}
        )

        return {"message": "Word re-assigned to wordlist successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# INES from MongoDB Analytics Report


@app.get("/api/mongo/analytics/difficult-words/{username}")
def mongo_get_difficult_words(username: str):
    mongo = get_mongo()
    try:
        user = mongo.users.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        difficult_words = [
            w for w in user.get("words", [])
            if w.get("is_new") == True
        ]

        if not difficult_words:
            return []

        result = []
        for w in difficult_words:
            wordlist = mongo.wordlists.find_one({"words": w["word_id"]})
            result.append({
                "username": user["username"],
                "word_to_learn": w["word"],
                "translation": w["translation"],
                "progress": w["correct_count"],
                "mistakes_count": w["mistakes_count"],
                "due_date": w.get("next_review"),
                "wordlist_name": wordlist["name"] if wordlist else "N/A"
            })

        result.sort(key=lambda x: x["mistakes_count"], reverse=True)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ANASTASIIA SQL Use Case


class AssignWordlistToUserRequest(BaseModel):
    user_id: int
    wordlist_id: int

@app.post("/api/assign-wordlist-to-user")
def assign_wordlist_to_user(request: AssignWordlistToUserRequest):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM Users WHERE user_id = %s", (request.user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="User not found")

            cursor.execute("SELECT * FROM Wordlists WHERE wordlist_id = %s", (request.wordlist_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Wordlist not found")

            cursor.execute(
                "SELECT * FROM Wordlist_Words WHERE wordlist_id = %s LIMIT 1",
                (request.wordlist_id,)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Wordlist is empty")

            cursor.execute("""
                INSERT IGNORE INTO User_Wordlists (user_id, wordlist_id)
                VALUES (%s, %s)
            """, (request.user_id, request.wordlist_id))

            cursor.execute("""
                INSERT IGNORE INTO User_Words (user_id, word_id)
                SELECT %s, wl.word_id
                FROM Wordlist_Words wl
                JOIN Words w ON wl.word_id = w.word_id
                WHERE wl.wordlist_id = %s
            """, (request.user_id, request.wordlist_id))

            db.commit()
            return {"message": "Wordlist assigned to user successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()