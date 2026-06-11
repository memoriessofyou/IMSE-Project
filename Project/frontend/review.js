let reviewSessionId = null;
let currentWord = null;
let sessionCorrect = 0;
let sessionWrong = 0;

async function toggleReviewModal() {
    const modal = document.getElementById('review-modal');
    const content = document.getElementById('review-content');
    
    if (modal.classList.contains('flex')) {
        closeReviewModal();
        return;
    }

    if (!selectedUser) {
        alert('Please select a user first.');
        return;
    }


    sessionCorrect = 0;
    sessionWrong = 0;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    content.innerHTML = '<div class="flex flex-col items-center"><div class="animate-spin rounded-full h-10 w-10 border-b-2 border-fjord-blue mb-4"></div><p class="text-gray-500 font-medium">Starting session...</p></div>';

    try {
        const res = await fetch('/api/review/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: parseInt(selectedUser) })
        });
        
        if (!res.ok) {
            const err = await res.json();
            content.innerHTML = `<p class="text-red-500 text-center font-medium">${err.detail || 'Error starting session'}</p>`;
            return;
        }

        const data = await res.json();
        
        if (data.message && data.message.includes("No words")) {
            displayFinishedSession(data.message);
            return;
        }

        reviewSessionId = data.session_id;
        loadNextWord();
    } catch (err) {
        content.innerHTML = '<p class="text-red-500 text-center font-medium">Failed to connect to backend.</p>';
    }
}

function closeReviewModal() {
    const modal = document.getElementById('review-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    if (reviewSessionId) {
        fetch(`/api/review/end?session_id=${reviewSessionId}`, { method: 'POST' });
        reviewSessionId = null;
    }

    if (typeof window.loadDetailedReport === 'function') {
        window.loadDetailedReport();
    }
}

async function loadNextWord() {
    const content = document.getElementById('review-content');
    try {
        const res = await fetch(`/api/review/next-word?user_id=${selectedUser}`);
        const data = await res.json();

        if (data.finished) {
            displayFinishedSession();
            return;
        }

        currentWord = data;
        content.innerHTML = `
            <div class="text-4xl font-bold text-fjord-blue text-center mb-10 transition-all">${data.word}</div>
            <div id="translation" class="hidden text-2xl text-green-600 text-center mb-10 font-medium">${data.translation}</div>
            <div class="flex flex-col space-y-3" id="action-buttons">
                <button onclick="showTranslation()" class="w-full py-3 bg-fjord-blue text-white rounded-xl font-semibold hover:bg-fjord-blue-light transition-all shadow-md">
                    Show Translation
                </button>
            </div>
        `;
    } catch (err) {
        content.innerHTML = '<p class="text-red-500 text-center font-medium">Error loading word.</p>';
    }
}

function displayFinishedSession(customMessage) {
    const content = document.getElementById('review-content');

    let html = `
        <h2 class="text-3xl font-bold text-green-600 text-center mb-4">Session Complete!</h2>
        <p class="text-center text-slate-text font-medium text-lg mb-8">
            No words for today! Come back tomorrow :)
        </p>
        
        <div class="flex justify-center items-center space-x-8 mb-10">
            <div class="text-center">
                <p class="text-xs text-green-600 font-bold uppercase tracking-wider mb-1">Right</p>
                <p class="text-4xl font-black text-green-600">${sessionCorrect}</p>
            </div>
            <div class="h-12 w-px bg-gray-200"></div>
            <div class="text-center">
                <p class="text-xs text-red-500 font-bold uppercase tracking-wider mb-1">Wrong</p>
                <p class="text-4xl font-black text-red-500">${sessionWrong}</p>
            </div>
        </div>

        <button onclick="closeReviewModal()" class="w-full py-4 bg-fjord-blue text-white font-bold rounded-xl hover:bg-fjord-blue-light transition-all shadow-md">
            Return to Dashboard
        </button>
    `;
    
    content.innerHTML = html;
}

function showTranslation() {
    document.getElementById('translation').classList.remove('hidden');
    document.getElementById('action-buttons').innerHTML = `
        <div class="grid grid-cols-2 gap-4">
            <button onclick="submitResult(true)" class="py-3 bg-green-500 text-white rounded-xl font-bold hover:bg-green-600 transition-all shadow-md">
                Correct
            </button>
            <button onclick="submitResult(false)" class="py-3 bg-red-500 text-white rounded-xl font-bold hover:bg-red-600 transition-all shadow-md">
                Incorrect
            </button>
        </div>
    `;
}

async function submitResult(isCorrect) {
    const content = document.getElementById('review-content');
    
    if (isCorrect) sessionCorrect++;
    else sessionWrong++;

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
            content.innerHTML = `<div class="flex flex-col items-center">
                <div class="animate-pulse text-green-600 font-bold text-xl">${isCorrect ? 'Brilliant!' : 'Keep going!'}</div>
                <p class="text-gray-400 text-sm mt-2">Next word coming up...</p>
            </div>`;
            setTimeout(loadNextWord, 600);
        } else {
            content.innerHTML = '<p class="text-red-500 text-center">Error submitting result.</p>';
        }
    } catch (err) {
        content.innerHTML = '<p class="text-red-500 text-center">Network error.</p>';
    }
}
