-- db/init.sql

CREATE TABLE IF NOT EXISTS Users (
    user_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    total_xp INT UNSIGNED DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Admin_Users (
    user_id INT UNSIGNED NOT NULL PRIMARY KEY,
    email VARCHAR(100),
    last_admin_access TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Basic_Users (
    user_id INT UNSIGNED NOT NULL PRIMARY KEY,
    daily_word_limit INT UNSIGNED DEFAULT 20,
    is_trial_used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Premium_Users (
    user_id INT UNSIGNED NOT NULL PRIMARY KEY,
    subscription_expiry DATE,
    plan_type VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Topics (
    topic_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS Words (
    word_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    word VARCHAR(255) NOT NULL,
    translation VARCHAR(255) NOT NULL,
    difficulty_level TINYINT UNSIGNED,
    base_word_id INT UNSIGNED DEFAULT NULL,
    FOREIGN KEY (base_word_id) REFERENCES Words(word_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Wordlists (
    wordlist_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    difficulty_level TINYINT UNSIGNED,
    topic_id INT UNSIGNED NOT NULL,
    FOREIGN KEY (topic_id) REFERENCES Topics(topic_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Achievements (
    achievement_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    xp_bonus INT UNSIGNED DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Learning_Sessions (
    session_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    session_type VARCHAR(50),
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP NULL,
    words_count INT UNSIGNED DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Wordlist_Words (
    wordlist_id INT UNSIGNED NOT NULL,
    word_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (wordlist_id, word_id),
    FOREIGN KEY (wordlist_id) REFERENCES Wordlists(wordlist_id) ON DELETE CASCADE,
    FOREIGN KEY (word_id) REFERENCES Words(word_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS User_Wordlists (
    user_id INT UNSIGNED NOT NULL,
    wordlist_id INT UNSIGNED NOT NULL,
    enrolled_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, wordlist_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (wordlist_id) REFERENCES Wordlists(wordlist_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS User_Achievements (
    user_id INT UNSIGNED NOT NULL,
    achievement_id INT UNSIGNED NOT NULL,
    earned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, achievement_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (achievement_id) REFERENCES Achievements(achievement_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS User_Words (
    user_id INT UNSIGNED NOT NULL,
    word_id INT UNSIGNED NOT NULL,
    is_new BOOLEAN DEFAULT TRUE,
    problematic BOOLEAN DEFAULT FALSE,
    next_review TIMESTAMP NULL DEFAULT NULL,
    last_reviewed TIMESTAMP NULL DEFAULT NULL,
    `interval` INT UNSIGNED DEFAULT 0,
    correct_count INT UNSIGNED DEFAULT 0,
    mistakes_count INT UNSIGNED DEFAULT 0,
    last_mistake TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (user_id, word_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (word_id) REFERENCES Words(word_id) ON DELETE CASCADE
);