START TRANSACTION;

INSERT INTO user_wordlists (user_id, wordlist_id)
VALUES (1, 1);

INSERT INTO user_words (user_id, word_id)
SELECT 1, wl.word_id
FROM wordlist_words wl
JOIN words w ON wl.word_id = w.word_id
WHERE wl.wordlist_id = 1;

COMMIT;


