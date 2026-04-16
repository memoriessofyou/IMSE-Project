SELECT
    u.username,
    w.word,
    t.name AS topic_name,
    uw.correct_count,
    uw.mistakes_count,
    uw.next_review,
    ls.session_type,
    ls.words_count AS last_session_volume
FROM Users u
JOIN User_Words uw ON u.user_id = uw.user_id
JOIN Words w ON uw.word_id = w.word_id
JOIN Wordlist_Words ww ON w.word_id = ww.word_id
JOIN Wordlists wl ON ww.wordlist_id = wl.wordlist_id
JOIN Topics t ON wl.topic_id = t.topic_id
JOIN Learning_Sessions ls ON u.user_id = ls.user_id and DATE(uw.last_reviewed) = DATE(ls.start_time)
WHERE u.username = 'Bella'
  AND ls.session_id = (SELECT MAX(session_id) FROM Learning_Sessions WHERE user_id = u.user_id)
ORDER BY t.name, uw.next_review;