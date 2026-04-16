UPDATE User_Words 
SET is_new = TRUE, 
    correct_count = 0, 
    `interval` = 0,
    problematic = TRUE
WHERE user_id = 1 AND word_id = 1;

INSERT INTO Wordlist_Words (wordlist_id, word_id) 
VALUES (1, 1);