INSERT INTO topics (topic_id, name) VALUES (1, 'Sample topic');

INSERT INTO wordlists (wordlist_id, name, topic_id) VALUES (1, 'Første fraser',1), (2, 'Fraser i klasserommet',1), (3, 'Daglige aktiviteter',1), (4, 'Tall',1), (5, 'Viktige substantiver',1), (6, 'Viktige verb',1);

INSERT INTO words (word_id, word, translation, difficulty_level) VALUES (1, 'hei', 'hi', 1), (2, 'hallo', 'hello', 1), (3, 'god morgen', 'good morning', 1), (4, 'god dag', 'good day', 1), (5, 'god kveld', 'good evening', 1), (6, 'god natt', 'good night', 1);

INSERT INTO wordlist_words (word_id, wordlist_id) VALUES (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1);

INSERT INTO users (user_id, username) VALUES (1, 'user1'), (2, 'user2'), (3, 'user3');