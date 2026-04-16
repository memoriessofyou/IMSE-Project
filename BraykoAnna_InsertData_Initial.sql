#use language_app;

insert into users(username) VALUES ('Bella');

INSERT INTO Words (word, translation, difficulty_level, base_word_id) VALUES
('Jeg', 'I', 1, NULL),
('Jente', 'Girl', 1, NULL),
('Ost', 'Cheese', 1, NULL),
('Kjøtt', 'Meat', 2, NULL);

INSERT INTO Words (word, translation, difficulty_level, base_word_id) VALUES
('Genta', 'The girl (Høgnorsk)', 2, 2),
('Kjøt', 'Meat (Nynorsk)', 2, 4);

INSERT INTO Topics (name, description)
VALUES ('Norsk Hverdag','Common vocabulary and phrases used in daily Norwegian life.');

INSERT INTO Wordlists (name, description, difficulty_level, topic_id)
VALUES ('Hilsener og Introduksjoner','Learn how to say hello, goodbye, and introduce yourself.', 1,1);

INSERT INTO Wordlists (name, description, difficulty_level, topic_id)
VALUES ('Mat og Drikke','Essential words for ordering at a cafe or grocery shopping.',2,1);

INSERT INTO wordlist_words(wordlist_id, word_id) VALUES
(1,1), (1,2),(1,5),
(2,3),(2,4),(2,6);

INSERT INTO User_Words ( user_id, word_id, is_new, problematic, next_review, last_reviewed,
    `interval`, correct_count, mistakes_count,  last_mistake ) VALUES
(1, 1, 0, 1, NOW(), NOW() - interval 6 DAY, 2, 1,
 3, NOW() - INTERVAL 6 DAY),
(1, 2, 0, 0, NOW(), NOW() - interval 6 DAY, 3,
 3, 1, NOW() - INTERVAL 13 DAY),
(1, 3, 1, 0, NOW(), NULL, 0, 0, 0, NULL),
(1, 4, 1, 0, NOW(), NULL, 0, 0, 0, NULL),
(1, 5, 1, 0, NOW(), NULL, 0, 0, 0, NULL),
(1, 6, 1, 0, NOW(), NULL, 0, 0, 0, NULL);


INSERT INTO user_wordlists(user_id, wordlist_id, enrolled_at) VALUES
(1,1,NOW() - INTERVAL 30 DAY), (1,2,NOW());
