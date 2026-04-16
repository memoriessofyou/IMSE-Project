
INSERT INTO Topics (name, description) VALUES ('Food', 'Vocabulary for eating and cooking');
INSERT INTO Words (translation, difficulty_level) VALUES ('Melk (Milk)', 1); 
INSERT INTO Users (username, total_xp) VALUES ('MaxMustermann', 100);

INSERT INTO Wordlists (name, topic_id) VALUES ('Difficult Words', 1);

INSERT INTO User_Words (user_id, word_id, is_new, correct_count, `interval`) 
VALUES (1, 1, FALSE, 5, 10);