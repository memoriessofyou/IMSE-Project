# API for the project


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pymysql
from dotenv import load_dotenv
import random
from datetime import datetime, timedelta
from pydantic import BaseModel

import os

load_dotenv()

from review_endpoints import router as review_router

app = FastAPI(
    title = "Norwegian Learning App",
    description = "Group Project for the course IMSE"
)

app.include_router(review_router)

# to let frontend connect with backend we use a middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def get_mongo():
    # get mongo based on .env file
    return




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
    # Join with subtype tables to determine the user type
    sql = """
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
    """
    cursor.execute(sql)
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

from db_generator import generate_data

@app.post("/api/seed")
def seed_database():
    success = generate_data()
    if success:
        return {"message": "Database seeded successfully"}
    else:
        raise HTTPException(status_code=500, detail="Error seeding database")



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


            # first we see if the user exists
            cursor.execute(f"SELECT * FROM Users WHERE user_id = {request.user_id}")
            if not cursor.fetchone():
                raise HTTPException(status_code= 400, detail= "USER NOT FOUND")


            # we see if the word is in the DB
            cursor.execute(f"SELECT * FROM Words WHERE word_id = {request.word_id}")
            if not cursor.fetchone():
                raise HTTPException(status_code= 400, detail= "WORD NOT FOUND")

            # we check for the wordlist
            cursor.execute(f"SELECT * FROM Wordlists WHERE wordlist_id = {request.wordlist_id}")
            if not cursor.fetchone():
                raise HTTPException(status_code= 400, detail= "WORDLIST NOT FOUND")

            # if everything worked well we can re-assign the word to the word list

            # we update the users progress on that word
            cursor.execute(f"UPDATE User_Words SET is_new = TRUE, correct_count = 0 WHERE user_id = {request.user_id} AND word_id = {request.word_id}")

            # we re-link the word to the wordlist

            cursor.execute(f"INSERT INTO Wordlist_Words(wordlist_id, word_id) VALUES {request.wordlist_id, request.word_id}")

            # commit the changes
            db.commit()
            return {"msg": "Word  re-assigned to the users wordlist successfully" }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code= 500, detail = e)
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

