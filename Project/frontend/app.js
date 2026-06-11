// Application State
let appState = {
    selectedUser: null,
    selectedUsername: 'User',
    currentMode: 'Student', // Admin or Student
    users: []
};

// DOM Elements
const navUserDisplay = document.getElementById('nav-user-display');
const userDropdownList = document.getElementById('user-dropdown-list');
const profileDropdown = document.getElementById('profile-dropdown');
const profileDropdownBtn = document.getElementById('profile-dropdown-btn');

const adminView = document.getElementById('admin-view');
const studentView = document.getElementById('student-view');
const emptyView = document.getElementById('empty-view');

const adminWelcome = document.getElementById('admin-welcome');
const studentWelcome = document.getElementById('student-welcome');
const seedBanner = document.getElementById('seed-banner');
const detailedReportContainer = document.getElementById('detailed-report-container');

// Initialize Application
async function init() {
    await loadUsers();
    setupDropdown();
    
    // Check localStorage for previous session
    const savedId = localStorage.getItem('selected_user_id');
    const savedName = localStorage.getItem('selected_username');
    if (savedId && savedName) {
        // Find user type
        const user = appState.users.find(u => u.user_id == savedId);
        selectUser(savedId, savedName, user ? user.user_type : 'Basic');
    }
}

// Setup Profile Dropdown Toggle
function setupDropdown() {
    profileDropdownBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        profileDropdown.classList.toggle('hidden');
    });

    document.addEventListener('click', () => {
        profileDropdown.classList.add('hidden');
    });
}

// Load users from API
async function loadUsers() {
    try {
        const res = await fetch('/api/users');
        const users = await res.json();
        appState.users = users;
        renderUserDropdown();
    } catch (err) {
        console.error('Failed to load users:', err);
    }
}

// Render users into the dropdown
function renderUserDropdown() {
    userDropdownList.innerHTML = '';
    
    // Also populate the admin log filter if it exists
    const logFilter = document.getElementById('log-user-filter');
    if (logFilter) {
        logFilter.innerHTML = '<option value="">All Users</option>';
    }

    appState.users.forEach(u => {
        const btn = document.createElement('button');
        btn.className = 'block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-nordic-gray transition-colors';
        btn.textContent = `${u.username} (${u.user_type})`;
        btn.onclick = () => selectUser(u.user_id, u.username, u.user_type);
        userDropdownList.appendChild(btn);

        if (logFilter && u.user_type !== 'Admin') {
            const opt = document.createElement('option');
            opt.value = u.user_id;
            opt.textContent = `${u.username} (${u.user_type})`;
            logFilter.appendChild(opt);
        }
    });
}

// Select User and update UI
function selectUser(id, username, type = 'Basic') {
    appState.selectedUser = id;
    appState.selectedUsername = username;
    selectedUser = id; // Global for review.js

    localStorage.setItem('selected_user_id', id);
    localStorage.setItem('selected_username', username);

    navUserDisplay.textContent = username;
    adminWelcome.textContent = `Hello, ${username}!`;
    
    // Add streak to student welcome
    const streakDays = Math.floor(Math.random() * 15) + 1; // Simulated streak for visual effect
    
    let welcomeHtml = `
        <span>Welcome back, ${username}!</span>
        <span class="text-xl font-bold text-orange-500 bg-orange-100 px-3 py-1 rounded-full shadow-sm">🔥 ${streakDays} Day Streak!</span>
    `;

    // Add remaining words counter for Basic users
    if (type === 'Basic') {
        const remainingWords = Math.floor(Math.random() * 20); // Random 0-19 remaining
        welcomeHtml += `
            <span class="text-base font-bold text-fjord-blue bg-blue-50 border border-blue-100 px-3 py-1 rounded-full shadow-sm ml-2">
                Free words left today: ${remainingWords}
            </span>
        `;
    }
    
    studentWelcome.innerHTML = welcomeHtml;

    // Auto-switch mode based on user type if not manually set
    if (type === 'Admin') {
        appState.currentMode = 'Admin';
    } else {
        appState.currentMode = 'Student';
    }

    updateView();
}

// Manually set App Mode
function setAppMode(mode) {
    if (!appState.selectedUser) {
        alert('Please select a user first.');
        return;
    }
    appState.currentMode = mode;
    updateView();
}

// Toggle Views based on State
function updateView() {
    emptyView.classList.add('hidden');
    adminView.classList.add('hidden');
    studentView.classList.add('hidden');

    if (!appState.selectedUser) {
        emptyView.classList.remove('hidden');
    } else if (appState.currentMode === 'Admin') {
        adminView.classList.remove('hidden');
        loadSessionLogs(); // Load logs when switching to admin
    } else {
        studentView.classList.remove('hidden');
        loadDetailedReport(); // Load report when switching to student
    }
}

// Load Admin Session Logs
window.loadSessionLogs = async function() {
    const userId = document.getElementById('log-user-filter').value;
    const date = document.getElementById('log-date-filter').value;
    const tbody = document.getElementById('session-logs-tbody');
    
    if (!tbody) return;

    let url = '/api/admin/session-logs?';
    if (userId) url += `user_id=${userId}&`;
    if (date) url += `date=${date}`;
    
    try {
        const res = await fetch(url);
        const logs = await res.json();
        
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-10 text-center text-gray-400 font-medium">No session logs found.</td></tr>';
            return;
        }
        
        let html = '';
        logs.forEach(log => {
            html += `
                <tr class="hover:bg-gray-50 transition-colors bg-card-white">
                    <td class="px-6 py-4 text-gray-500 text-sm">${log.session_date}</td>
                    <td class="px-6 py-4 font-bold text-fjord-blue">${log.username}</td>
                    <td class="px-6 py-4 text-gray-600 font-medium">${log.topic_name}</td>
                    <td class="px-6 py-4 text-center font-bold text-slate-text">${log.words_practiced}</td>
                    <td class="px-6 py-4 text-center text-green-600 font-bold">${log.total_correct}</td>
                    <td class="px-6 py-4 text-center text-red-500 font-bold">${log.total_mistakes}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error('Failed to load session logs:', err);
        tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-10 text-center text-red-500">Error loading logs.</td></tr>';
    }
}

// Load Detailed Report for Dashboard
window.loadDetailedReport = async function() {
    if (!appState.selectedUser || !detailedReportContainer) return;
    
    try {
        const res = await fetch(`/api/review/session-report?user_id=${appState.selectedUser}`);
        const data = await res.json();
        
        if (data.length === 0) {
            detailedReportContainer.innerHTML = '<p class="text-gray-400 text-center py-10 font-medium">No recent session data. Start a review to see progress!</p>';
            return;
        }

        let html = `
            <table class="w-full text-left text-sm whitespace-nowrap">
                <thead class="bg-snow-white sticky top-0 border-b border-gray-100">
                    <tr>
                        <th class="px-6 py-4 font-semibold text-slate-text text-base">Word</th>
                        <th class="px-6 py-4 font-bold text-center text-xl"><span class="text-purple-600">✔️</span></th>
                        <th class="px-6 py-4 font-bold text-center text-xl"><span class="text-red-500">❌</span></th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-50">
        `;

        data.forEach(row => {
            html += `
                <tr class="hover:bg-gray-50 transition-colors bg-card-white">
                    <td class="px-6 py-5 font-semibold text-fjord-blue text-base">${row.word}</td>
                    <td class="px-6 py-5 text-center text-green-600 font-bold text-base">${row.correct_count}</td>
                    <td class="px-6 py-5 text-center text-red-500 font-bold text-base">${row.mistakes_count}</td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        detailedReportContainer.innerHTML = html;
    } catch (err) {
        console.error('Failed to load detailed report:', err);
        detailedReportContainer.innerHTML = '<p class="text-red-500 text-center py-10">Error loading report.</p>';
    }
}

// Seed Database logic
async function seedDatabase() {
    seedBanner.classList.remove('hidden');
    try {
        const res = await fetch('/api/seed', { method: 'POST' });
        const data = await res.json();
        seedBanner.classList.add('hidden');
        alert(data.message || 'Database seeded successfully!');
        await loadUsers();
    } catch (err) {
        seedBanner.classList.add('hidden');
        alert('Error seeding database.');
    }
}

// Start App
init();
