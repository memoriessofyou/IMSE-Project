SELECT 
    u.username, 
    w.translation, 
    uw.is_new, 
    uw.correct_count
FROM Users u
JOIN User_Words uw ON u.user_id = uw.user_id
JOIN Words w ON uw.word_id = w.word_id
WHERE u.username = 'MaxMustermann' AND w.translation LIKE '%Melk%';