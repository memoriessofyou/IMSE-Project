let reviewSessionId = null;
let currentWord = null;

async function toggleReviewModal() {
    const modal = document.getElementById('review-modal');
    const content = document.getElementById('review-content');
    
    if (modal.style.display === 'flex') {
        closeReviewModal();
        return;
    }

    if (!selectedUser) {
        alert('Please select a user first.');
        return;
    }

    modal.style.display = 'flex';
    content.innerHTML = '<p>Starting session...</p>';

    try {
        const res = await fetch('/api/review/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: parseInt(selectedUser) })
        });
        
        if (!res.ok) {
            const err = await res.json();
            content.innerHTML = `<p class="error">${err.detail || 'Error starting session'}</p>`;
            return;
        }

        const data = await res.json();
        reviewSessionId = data.session_id;
        loadNextWord();
    } catch (err) {
        content.innerHTML = '<p class="error">Failed to connect to backend.</p>';
    }
}

function closeReviewModal() {
    document.getElementById('review-modal').style.display = 'none';
    if (reviewSessionId) {
        fetch(`/api/review/end?session_id=${reviewSessionId}`, { method: 'POST' });
        reviewSessionId = null;
    }
}

async function loadNextWord() {
    const content = document.getElementById('review-content');
    try {
        const res = await fetch(`/api/review/next-word?user_id=${selectedUser}`);
        const data = await res.json();

        if (data.finished) {
            const reportRes = await fetch(`/api/review/session-report?user_id=${selectedUser}`);
            const reportData = await reportRes.json();
            
            let reportHtml = `
                <p style="text-align:center; color: #2c3e50; font-weight: bold; font-size: 1.1rem; margin-bottom: 10px;">
                    No words for today! Come back tomorrow :)
                </p>
                <p style="text-align:center; color: #27ae60; font-weight: bold; font-size: 1.2rem; margin-bottom: 15px;">Session Complete!</p>
                
                <div style="max-height: 300px; overflow-y: auto; border: 1px solid #eee; border-radius: 5px;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
                        <thead style="background: #f8f9fa; position: sticky; top: 0;">
                            <tr>
                                <th style="padding: 8px; border-bottom: 1px solid #eee; text-align: left;">Word</th>
                                <th style="padding: 8px; border-bottom: 1px solid #eee; text-align: left;">Topic</th>
                                <th style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">✔️</th>
                                <th style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">❌</th>
                                <th style="padding: 8px; border-bottom: 1px solid #eee; text-align: left;">Next</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            if (reportData.length === 0) {
                reportHtml += '<tr><td colspan="5" style="padding: 20px; text-align: center; color: #999;">No detailed data for this session.</td></tr>';
            } else {
                reportData.forEach(row => {
                    const nextDate = row.next_review ? new Date(row.next_review).toLocaleDateString() : 'N/A';
                    reportHtml += `
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>${row.word}</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">${row.topic_name}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">${row.correct_count}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">${row.mistakes_count}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">${nextDate}</td>
                        </tr>
                    `;
                });
            }

            reportHtml += `
                        </tbody>
                    </table>
                </div>
                <div style="margin-top: 15px; font-size: 0.9rem; color: #666;">
                    Last Session Volume: ${reportData.length > 0 ? reportData[0].last_session_volume : 0} words
                </div>
                <button onclick="closeReviewModal()" style="width:100%; margin-top:20px; padding: 12px; background: #2c3e50; color: white; border: none; border-radius: 5px; cursor: pointer;">Close</button>
            `;
            
            content.innerHTML = reportHtml;
            return;
        }

        currentWord = data;
        content.innerHTML = `
            <div class="review-word">${data.word}</div>
            <div id="translation" class="review-translation">${data.translation}</div>
            <div class="review-actions" id="action-buttons">
                <button onclick="showTranslation()" style="padding: 10px 20px;">Show Translation</button>
            </div>
        `;
    } catch (err) {
        content.innerHTML = '<p class="error">Error loading word.</p>';
    }
}

function showTranslation() {
    document.getElementById('translation').style.display = 'block';
    document.getElementById('action-buttons').innerHTML = `
        <button class="btn-success" onclick="submitResult(true)" style="padding: 10px 25px;">Correct</button>
        <button class="btn-danger" onclick="submitResult(false)" style="padding: 10px 25px;">Incorrect</button>
    `;
}

async function submitResult(isCorrect) {
    const content = document.getElementById('review-content');
    try {
        const res = await fetch('/api/review/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: parseInt(selectedUser),
                word_id: currentWord.word_id,
                session_id: reviewSessionId,
                is_correct: isCorrect
            })
        });

        if (res.ok) {
            content.innerHTML = '<p style="text-align:center; color: #27ae60; font-size: 1.1rem;">Updating...</p>';
            setTimeout(loadNextWord, 500);
        } else {
            content.innerHTML = '<p class="error">Error submitting result.</p>';
        }
    } catch (err) {
        content.innerHTML = '<p class="error">Network error.</p>';
    }
}
