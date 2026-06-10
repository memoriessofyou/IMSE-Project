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

app = FastAPI(
    title = "Norwegian Learning App",
    description = "Group Project for the course IMSE"
)

# to let frontend connect with backend we use a middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------ Mongo ----------------------------------
def get_mongo():
    client = MongoClient(
        host=os.getenv("MONGO_HOST", "mongodb"),
        port=int(os.getenv("MONGO_PORT", 27017))
    )
    return client["language_app"]


# Mongo migration endpoint

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

                # get wordlists assigned to this user
                cursor.execute("""
                    SELECT wordlist_id FROM User_Wordlists
                    WHERE user_id = %s
                """, (uid,))
                user_wordlist_ids = [
                    r["wordlist_id"] for r in cursor.fetchall()
                ]

                # get word progress for this user
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


# connecting the database 

def get_db():
    # get the db based on the .env file
        return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "apppassword"),
        database=os.getenv("DB_NAME", "language_app"),
        cursorclass=pymysql.cursors.DictCursor
    )



@app.get("/api/words")
def get_all_words():
    
    try:
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM Words")
        return cursor.fetchall()
        
    except Exception as e:
        print(f"Database connection error: {e}")
    

@app.get("/api/words/{id}")
def get_specific_word(id: int):
    cursor = get_db().cursor()
    select_ms = "SELECT * FROM Words WHERE word_id = %(word_id)s"
    cursor.execute(select_ms, {'word_id': 2})
    return cursor.fetchall()

@app.get("/api/users")
def get_all_users():
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM Users")
    return cursor.fetchall()

@app.get("/api/users/{id}")
def get_specific_user(id: int):
    cursor = get_db().cursor()
    select_ms = "SELECT * FROM Users WHERE user_id = %(user_id)s"
    cursor.execute( select_ms, {'user_id': 2})
    return cursor.fetchall()

@app.get("/api/wordlist")
def get_all_wordlists():
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM Wordlists")
    return cursor.fetchall()

@app.get("/api/wordlist/{id}")
def get_specific_wordlist(id: int):
    cursor = get_db().cursor()
    select_ms = "SELECT * FROM Wordlists WHERE wordlist_id = %s"
    cursor.execute( select_ms, (id,))
    return cursor.fetchall()

@app.get("/api/wordlist/{id}/words")
def get_wordlist_words(id: int):
    cursor = get_db().cursor()
    select_ms = "SELECT * FROM Wordlist_Words WHERE wordlist_id = %s"
    cursor.execute( select_ms, (id,))
    return cursor.fetchall()

@app.get("/api/topics")
def get_all_topics():
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM Topics")
    return cursor.fetchall()



# use cases endpoint

# get all words assigned to a user
@app.get("/api/users/{id}/words")
def get_words_from_user(id: int):
    cursor = get_db().cursor()
    select_ms = """
        SELECT w.word_id, w.word, w.translation, uw.is_new, uw.correct_count,
                            uw.mistakes_count, uw.next_review, uw.last_reviewed,
                            uw.problematic
        FROM User_Words uw
        JOIN Words w ON w.word_id = uw.word_id
        WHERE uw.user_id = %s
        """
    cursor.execute(select_ms, (id,))
    return cursor.fetchall()

# get all wordlists assigned to a user
@app.get("/api/users/{id}/wordlist")
def get_wordlist_from_user(id: int):
    cursor = get_db().cursor()
    select_ms = """
        SELECT wl.wordlist_id, wl.name
        FROM User_Wordlists uw
        JOIN Wordlists wl ON wl.wordlist_id = uw.wordlist_id
        WHERE uw.user_id = %s
        """
    cursor.execute(select_ms, (id,))
    return cursor.fetchall()


# SEED POINT TO START WORKING WITH REAL DATA 

@app.post("/api/seed")
def seed_database():
    db = get_db()
    try:
        with db.cursor() as cursor:

            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table in [
                "User_Words", "User_Wordlists", "User_Achievements",
                "Wordlist_Words", "Learning_Sessions",
                "Words", "Wordlists", "Topics",
                "Users", "Achievements",
                "Admin_Users", "Basic_Users", "Premium_Users"
            ]:
                cursor.execute(f"DELETE FROM {table}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            db.commit()
            topics = [
                ("Food & Drink", "Common food and drink vocabulary"),
                ("Travel", "Words for getting around"),
                ("Daily Life", "Everyday Norwegian words"),
                ("Numbers & Time", "Counting and telling time"),
                ("Nature", "Animals, plants, weather"),
            ]
            cursor.executemany(
                "INSERT INTO Topics (name, description) VALUES (%s, %s)",
                topics
            )
            db.commit()

            words = [
                ("hei", "hello", 1, None),
                ("takk", "thank you", 1, None),
                ("vann", "water", 1, None),
                ("melk", "milk", 1, None),
                ("brød", "bread", 1, None),
                ("hus", "house", 1, None),
                ("bil", "car", 2, None),
                ("bok", "book", 1, None),
                ("hund", "dog", 1, None),
                ("katt", "cat", 1, None),
                ("stor", "big", 2, None),
                ("liten", "small", 2, None),
                ("god morgen", "good morning", 1, None),
                ("god natt", "good night", 1, None),
                ("ja", "yes", 1, None),
                ("nei", "no", 1, None),
                ("vær så snill", "please", 2, None),
                ("unnskyld", "excuse me", 2, None),
                ("skole", "school", 2, None),
                ("arbeid", "work", 2, None),
            ]
            cursor.executemany(
                """INSERT INTO Words 
                   (word, translation, difficulty_level, base_word_id) 
                   VALUES (%s, %s, %s, %s)""",
                words
            )
            db.commit()

            wordlists = [
                ("Basics", "Essential Norwegian phrases", 1, 1),
                ("Food Vocabulary", "Words for food and drink", 1, 1),
                ("Daily Phrases", "Common daily expressions", 2, 3),
                ("Intermediate", "For learners moving forward", 2, 2),
            ]
            cursor.executemany(
                """INSERT INTO Wordlists 
                   (name, description, difficulty_level, topic_id) 
                   VALUES (%s, %s, %s, %s)""",
                wordlists
            )
            db.commit()

            wordlist_words = [
                (1, 1), (1, 2), (1, 3), (1, 13), (1, 14),
                (2, 3), (2, 4), (2, 5),
                (3, 15), (3, 16), (3, 17), (3, 18),
                (4, 7), (4, 8), (4, 11), (4, 12),
            ]
            cursor.executemany(
                "INSERT INTO Wordlist_Words (wordlist_id, word_id) VALUES (%s, %s)",
                wordlist_words
            )
            db.commit()
            usernames = [
                "anna_b", "ines_t", "anastasiia_k",
                "erik_n", "sofia_l", "max_m",
                "lena_w", "jonas_h", "maria_s", "peter_r"
            ]
            for username in usernames:
                cursor.execute(
                    "INSERT INTO Users (username, total_xp) VALUES (%s, %s)",
                    (username, random.randint(0, 500))
                )
            db.commit()
            cursor.execute("SELECT user_id FROM Users")
            user_ids = [row["user_id"] for row in cursor.fetchall()]

            cursor.execute("SELECT wordlist_id FROM Wordlists")
            wordlist_ids = [row["wordlist_id"] for row in cursor.fetchall()]

            cursor.execute("SELECT word_id FROM Words")
            all_word_ids = [row["word_id"] for row in cursor.fetchall()]

            for user_id in user_ids:
                # assign 1-2 wordlists per user
                assigned_wl = random.sample(wordlist_ids, k=random.randint(1, 2))
                for wl_id in assigned_wl:
                    cursor.execute(
                        """INSERT IGNORE INTO User_Wordlists 
                           (user_id, wordlist_id) VALUES (%s, %s)""",
                        (user_id, wl_id)
                    )

                # assign 5-10 words per user with random progress
                assigned_words = random.sample(all_word_ids, k=random.randint(5, 10))
                for word_id in assigned_words:
                    correct = random.randint(0, 10)
                    mistakes = random.randint(0, 5)
                    is_new = 1 if correct == 0 else 0
                    next_review = datetime.now() + timedelta(days=random.randint(0, 7))
                    last_reviewed = datetime.now() - timedelta(days=random.randint(1, 10))
                    cursor.execute(
                        """INSERT IGNORE INTO User_Words
                           (user_id, word_id, is_new, correct_count,
                            mistakes_count, next_review, last_reviewed,
                            problematic, `interval`)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (user_id, word_id, is_new, correct, mistakes,
                         next_review, last_reviewed,
                         1 if mistakes > 3 else 0,
                         random.randint(1, 7))
                    )

            db.commit()
            return {"message": "Database seeded successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
        
        
        
# Ines Use Case: Assign word to wordlist

class AssignWordToWordListRequest(BaseModel):
    user_id : int
    word_id : int
    wordlist_id : int
    
# resets a difficult word for a user and re assigns it to her/his wordlist
@app.post("/api/assign-word-to-wordlist")
def assign_word_to_wordlist(request: AssignWordToWordListRequest):
    db = get_db()
    try:
        with db.cursor() as cursor:

            # check user exists
            cursor.execute("SELECT * FROM Users WHERE user_id = %s", (request.user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")

            # check word exists
            cursor.execute("SELECT * FROM Words WHERE word_id = %s", (request.word_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Word not found")

            # check wordlist exists
            cursor.execute("SELECT * FROM Wordlists WHERE wordlist_id = %s", (request.wordlist_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Wordlist not found")

            # reset word progress
            cursor.execute("""
                UPDATE User_Words
                SET is_new = TRUE,
                    correct_count = 0,
                    `interval` = 0
                WHERE user_id = %s AND word_id = %s
            """, (request.user_id, request.word_id))

            # re-link word to wordlist
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

# Anastasiia Use Case: Assign words to a user
class AssignWordlistToUserRequest(BaseModel):
    user_id : int
    wordlist_id : int
    
# assigns a wordlist and all words it contains to a user
@app.post("/api/assign-wordlist-to-user")
def assign_wordlist_to_user(request: AssignWordlistToUserRequest):
    db = get_db()
    try:
        with db.cursor() as cursor:
            # checking if user exists
            cursor.execute(f"SELECT * FROM Users WHERE user_id = %(user_id)s",
                           {"user_id": request.user_id})
            if not cursor.fetchone():
                raise HTTPException(status_code= 400, detail= "USER NOT FOUND")
            
            # checking if worlist exists
            cursor.execute(f"SELECT * FROM Wordlists WHERE wordlist_id = %(wordlist_id)s", {"wordlist_id": request.wordlist_id})
            if not cursor.fetchone():
                raise HTTPException(status_code= 400, detail= "WORDLIST NOT FOUND")
            
            # checking if the wordlist has at least 1 word assigned
            cursor.execute(f"SELECT * FROM Wordlist_Words WHERE wordlist_id = %(wordlist_id)s LIMIT 1", {"wordlist_id": request.wordlist_id})
            if not cursor.fetchone():
                raise HTTPException(status_code= 400, detail= "WORDLIST IS EMPTY")
                        
            #--- PRE-CHECK COMPLETE ---#    

            # assign wordlist to the user
            cursor.execute(f"INSERT IGNORE INTO User_Wordlists (user_id, wordlist_id) VALUES (%(user_id)s, %(wordlist_id)s)", 
                           {"user_id": request.user_id, "wordlist_id": request.wordlist_id})
            
            # assign relevant words to the user
            cursor.execute(
                f"""INSERT IGNORE INTO User_Words (user_id, word_id)
                    SELECT %(user_id)s, wl.word_id 
                    FROM Wordlist_Words wl 
                    JOIN Words w ON wl.word_id = w.word_id 
                    WHERE wl.wordlist_id = %(wordlist_id)s """, 
                           {"user_id": request.user_id, "wordlist_id": request.wordlist_id})
            
            # commit the changes
            db.commit()
            return {"msg": "Wordlist assigned to user successfully" }
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code= 500, detail = str(e))
    finally:
        db.close()

        
        
    

