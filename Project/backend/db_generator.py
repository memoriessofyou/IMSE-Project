import pymysql
import random
import os
from datetime import datetime, timedelta

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "apppassword"),
        database=os.getenv("DB_NAME", "language_app"),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def generate_data():
    db = get_db_connection()
    try:
        with db.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            all_tables = [
                "User_Words", "User_Wordlists", "User_Achievements",
                "Wordlist_Words", "Learning_Sessions", "Words",
                "Wordlists", "Topics", "Users", "Achievements",
                "Admin_Users", "Basic_Users", "Premium_Users"
            ]
            for table in all_tables:
                cursor.execute(f"DELETE FROM {table}")
            #ai stands for autoincrement, not all the table have them
            ai_tables = ["Learning_Sessions", "Words", "Wordlists", "Topics", "Users", "Achievements"]
            for table in ai_tables:
                cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")

            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            topic_data = [(f"Topic{i}", f"Description for Topic{i}") for i in range(1, 11)]
            cursor.executemany("INSERT INTO Topics (name, description) VALUES (%s, %s)", topic_data)
            
            cursor.execute("SELECT topic_id FROM Topics")
            topic_ids = [row['topic_id'] for row in cursor.fetchall()]

            #words
            norwegian_words = [
                ("hei", "hello"), ("takk", "thank you"), ("vann", "water"), ("melk", "milk"),
                ("brød", "bread"), ("hus", "house"), ("bil", "car"), ("bok", "book"),
                ("hund", "dog"), ("katt", "cat"), ("stor", "big"), ("liten", "small"),
                ("skole", "school"), ("arbeid", "work"), ("kaffe", "coffee"), ("te", "tea"),
                ("fly", "plane"), ("tog", "train"), ("frokost", "breakfast"), ("middag", "dinner"),
                ("eple", "apple"), ("banan", "banana"), ("ost", "cheese"), ("smør", "butter"),
                ("kniv", "knife"), ("gaffel", "fork"), ("skje", "spoon"), ("tallerken", "plate"),
                ("stol", "chair"), ("bord", "table"), ("seng", "bed"), ("vindu", "window"),
                ("dør", "door"), ("vegg", "wall"), ("tak", "roof"), ("gulv", "floor"),
                ("sol", "sun"), ("måте", "moon"), ("stjerne", "star"), ("himmel", "sky"),
                ("regn", "rain"), ("snø", "snow"), ("vind", "wind"), ("vær", "weather"),
                ("fjell", "mountain"), ("skog", "forest"), ("sjø", "sea"), ("elv", "river"),
                ("vei", "road"), ("gate", "street"), ("by", "city"), ("land", "country"),
                ("menneske", "human"), ("mann", "man"), ("kvinne", "woman"), ("barn", "child"),
                ("venn", "friend"), ("familie", "family"), ("mor", "mother"), ("far", "father"),
                ("bror", "brother"), ("søster", "sister"), ("dag", "day"), ("natt", "night"),
                ("morgen", "morning"), ("kveld", "evening"), ("uke", "week"), ("måned", "month"),
                ("år", "year"), ("tid", "time"), ("klokke", "clock"), ("penger", "money"),
                ("butikk", "shop"), ("pris", "price"), ("kjøpe", "buy"), ("selge", "sell"),
                ("glad", "happy"), ("trist", "sad"), ("sint", "angry"), ("redd", "afraid"),
                ("snill", "kind"), ("viktig", "important"), ("vanskelig", "difficult"), ("lett", "easy"),
                ("ny", "new"), ("gammel", "old"), ("rød", "red"), ("blå", "blue"),
                ("grønn", "green"), ("gul", "yellow"), ("svart", "black"), ("hvit", "white"),
                ("en", "one"), ("to", "two"), ("tre", "three"), ("fire", "four"),
                ("fem", "five"), ("seks", "six"), ("syv", "seven"), ("åtte", "eight"),
                ("ni", "nine"), ("ti", "ten"), ("hundre", "hundred"), ("tusen", "thousand")
            ]
            words_to_insert = [(w[0], w[1], random.randint(1, 3)) for w in norwegian_words]
            cursor.executemany(
                "INSERT INTO Words (word, translation, difficulty_level) VALUES (%s, %s, %s)",
                words_to_insert
            )
            
            cursor.execute("SELECT word_id FROM Words")
            word_ids = [row['word_id'] for row in cursor.fetchall()]

            #wordlists
            wordlist_data = []
            for i in range(1, 16):
                wordlist_data.append((f"Wordlist{i}", f"Description for Wordlist{i}", random.randint(1, 3), random.choice(topic_ids)))
            cursor.executemany("INSERT INTO Wordlists (name, description, difficulty_level, topic_id) VALUES (%s, %s, %s, %s)", wordlist_data)
            
            cursor.execute("SELECT wordlist_id FROM Wordlists")
            wordlist_ids = [row['wordlist_id'] for row in cursor.fetchall()]

            # Link words to wordlists
            for wl_id in wordlist_ids:
                sampled_words = random.sample(word_ids, random.randint(5, 15))
                for w_id in sampled_words:
                    cursor.execute("INSERT IGNORE INTO Wordlist_Words (wordlist_id, word_id) VALUES (%s, %s)", (wl_id, w_id))

            #users
            for i in range(1, 31):
                username = f"User{i}"
                cursor.execute("INSERT INTO Users (username, total_xp) VALUES (%s, %s)", (username, random.randint(0, 5000)))
                u_id = cursor.lastrowid
                
                # Assign types
                user_type = random.choice(["Admin", "Basic", "Premium"])
                if user_type == "Admin":
                    cursor.execute(
                        "INSERT INTO Admin_Users (user_id, email, last_admin_access) VALUES (%s, %s, %s)", 
                        (u_id, f"admin{i}@example.com", datetime.now())
                    )
                elif user_type == "Premium":
                    expiry = (datetime.now() + timedelta(days=random.randint(30, 365))).date()
                    cursor.execute(
                        "INSERT INTO Premium_Users (user_id, subscription_expiry, plan_type) VALUES (%s, %s, %s)", 
                        (u_id, expiry, random.choice(["Monthly", "Annual", "Lifetime"]))
                    )
                else: # Basic
                    cursor.execute(
                        "INSERT INTO Basic_Users (user_id, daily_word_limit, is_trial_used) VALUES (%s, %s, %s)", 
                        (u_id, 20, random.choice([1, 0]))
                    )

                # Generate sessions and word progress ONLY for non-admin users
                if user_type != "Admin":
                    # Generate multiple sessions spread over the last 45 days (including today)
                    num_words = random.randint(20, 50)
                    user_word_sample = random.sample(word_ids, num_words)
                    
                    sessions = []
                    for _ in range(random.randint(3, 8)):
                        session_date = datetime.now() - timedelta(days=random.randint(0, 45), hours=random.randint(0, 23))
                        sessions.append(session_date)
                    
                    # Sort chronologically so MAX(session_id) represents the most recent
                    sessions.sort()

                    for sess_date in sessions:
                        cursor.execute(
                            "INSERT INTO Learning_Sessions (user_id, session_type, start_time, end_time, words_count) VALUES (%s, %s, %s, %s, %s)",
                            (u_id, "Word Review", sess_date, sess_date + timedelta(minutes=15), random.randint(5, 15))
                        )
                    
                    # Distribute words randomly among all generated sessions
                    for word_id in user_word_sample:
                        correct = random.randint(0, 30)
                        mistakes = random.randint(0, 15)
                        
                        # Randomly pick which session this word was LAST reviewed in
                        chosen_session = random.choice(sessions)
                        last_reviewed = chosen_session + timedelta(seconds=random.randint(1, 60))
                        next_review = datetime.now() + timedelta(days=random.randint(-2, 10))
                        
                        cursor.execute("""
                            INSERT INTO User_Words 
                            (user_id, word_id, is_new, correct_count, mistakes_count, last_reviewed, next_review, problematic, `interval`)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            u_id, word_id, 0, correct, mistakes, last_reviewed, next_review,
                            1 if mistakes > 5 else 0, random.randint(1, 20)
                        ))

            db.commit()
            return True
    except Exception as e:
        db.rollback()
        print(f"FAILED: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    generate_data()
