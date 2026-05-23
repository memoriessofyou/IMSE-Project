# API for the project


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
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


DB = get_db()

@app.get("/api/words")
def get_all_words():
    
    try:
        cursor = DB.cursor()
        cursor.execute("SELECT * FROM WORDS")
        return cursor.fetchall()
        
    except Exception as e:
        print(f"Database connection error: {e}")
    

@app.get("api/words/{id}")
def get_specific_word(id: int):
    cursor = DB.cursor()
    select_ms = "SELECT * FROM WORDS WHERE ID = %(word_id)s"
    cursor.execute(select_ms, {'word_id': 2})
    return cursor.fetchall()

@app.get("api/users")
def get_all_users():
    cursor = DB.cursor()
    cursor.execute("SELECT * FROM USERS")
    return cursor.fetchall()

@app.get("api/users/{id}")
def get_specific_user(id: int):
    cursor = DB.cursor()
    select_ms = "SELECT * FROM USERS WHERE ID = %(user_id)s"
    cursor.execute( select_ms, {'user_id': 2})
    return cursor.fetchall()

@app.get("api/wordlist")
def get_all_wordlists():
    cursor = DB.cursor()
    cursor.execute("SELECT * FROM WORDLIST")
    return cursor.fetchall()

@app.get("api/topics")
def get_all_topics():
    cursor = DB.cursor()
    cursor.execute("SELECT * FROM TOPICS")
    return cursor.fetchall()



# use cases endpoint

@app.get("api/users/{id}/words")
def get_words_from_user():
    return

@app.get("api/users/{id}/wordlist")
def get_wordlist_from_user():
    return

