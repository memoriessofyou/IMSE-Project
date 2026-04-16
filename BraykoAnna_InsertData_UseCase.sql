#use language_app;

INSERT INTO learning_sessions(user_id, session_type) VALUES
    (1, 'Review');

update user_words set
    is_new = 0,
    problematic = 0,
    next_review = now() + INTERVAL `interval`DAY ,
    last_reviewed = now() ,
    `interval` = `interval` + 1,
    correct_count = correct_count +1 where user_id = 1 and  word_id IN (1,2,4);

update user_words
set is_new = 0,
    problematic = 1,
    next_review = now() + INTERVAL `interval`DAY,
    last_reviewed = now(),
    `interval` = 1,
    mistakes_count = mistakes_count + 1,
    last_mistake = now()
where user_id = 1 and  word_id IN (3,5,6);

update learning_sessions set end_time = now(), words_count = 6 where session_id = 2;