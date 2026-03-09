// ==================== CONFIGURATION ====================
// API_BASE_URL is defined in auth.js

// ==================== GLOBAL VARIABLES ====================
let currentUser = null;
let users = {};
let weeklyChart = null;
let monthlyChart = null;

// Activity recommendations data
const activityRecommendations = {
    mindfulness: {
        title: 'Mindfulness Meditation',
        description: 'Short mindfulness exercises to improve focus and reduce stress.',
        items: [
            '5-minute breathing exercise',
            'Body scan meditation',
            'Mindful walking practice',
            'Progressive muscle relaxation',
            'Loving-kindness meditation'
        ]
    },
    creative: {
        title: 'Creative Expression',
        description: 'Activities to boost creativity and self-expression.',
        items: [
            'Draw or paint your feelings',
            'Write a short poem',
            'Create a vision board',
            'Try digital art',
            'Make a gratitude collage'
        ]
    },
    exercise: {
        title: 'Physical Exercise',
        description: 'Quick and effective exercises to do anywhere.',
        items: [
            '10-minute yoga routine',
            'Desk stretches',
            'Jump rope for 5 minutes',
            'Bodyweight exercises',
            'Dance to your favorite song'
        ]
    },
    social: {
        title: 'Social Connection',
        description: 'Ideas to connect and engage with others.',
        items: [
            'Call a friend or family member',
            'Join an online community',
            'Plan a virtual meetup',
            'Write a thank-you note',
            'Share a positive story'
        ]
    },
    selfcare: {
        title: 'Self-Care Routine',
        description: 'Simple self-care activities to nurture yourself.',
        items: [
            'Take a warm bath',
            'Practice journaling',
            'Listen to calming music',
            'Enjoy a cup of herbal tea',
            'Get 7-9 hours of sleep'
        ]
    },
    learning: {
        title: 'Learning & Growth',
        description: 'Opportunities to learn something new and grow.',
        items: [
            'Take an online course',
            'Read a self-help book',
            'Learn a new language',
            'Watch educational videos',
            'Practice a new skill daily'
        ]
    }
};

// ==================== NOTIFICATION SYSTEM ====================
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full ${
        type === 'success' ? 'bg-green-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        type === 'warning' ? 'bg-yellow-500 text-black' :
        'bg-blue-500 text-white'
    }`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${
                type === 'success' ? 'fa-check-circle' :
                type === 'error' ? 'fa-exclamation-circle' :
                type === 'warning' ? 'fa-exclamation-triangle' :
                'fa-info-circle'
            } mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
        notification.classList.add('translate-x-0');
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ==================== LOCAL STORAGE MANAGEMENT ====================
function loadUsers() {
    const stored = localStorage.getItem('mindcare_users');
    if (stored) {
        try {
            users = JSON.parse(stored);
        } catch (e) {
            console.error('Failed to load users:', e);
            users = {};
        }
    }
}

function saveUsers() {
    localStorage.setItem('mindcare_users', JSON.stringify(users));
}

function saveCurrentUser() {
    if (currentUser) {
        localStorage.setItem('mindcare_current_user', JSON.stringify(currentUser));
    }
}

// ==================== API UTILITIES ====================
async function fetchFromAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        showNotification('Failed to connect to server. Please try again.', 'error');
        return null;
    }
}

// ==================== USER AUTHENTICATION ====================
async function handleRegistration(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const userData = {
        name: formData.get('name'),
        email: formData.get('email'),
        password: formData.get('password'),
        college: formData.get('college'),
        year: formData.get('year'),
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(formData.get('name'))}&background=random`
    };

    // Check if user already exists
    if (users[userData.email]) {
        showNotification('Email already registered!', 'error');
        return;
    }

    // Register via API
    const result = await fetchFromAPI('/register', {
        method: 'POST',
        body: JSON.stringify(userData)
    });

    if (result && result.success) {
        userData.id = result.data.id;
        users[userData.email] = userData;
        saveUsers();
        
        currentUser = userData;
        saveCurrentUser();
        
        showNotification('Registration successful!', 'success');
        document.getElementById('registrationPage').classList.remove('active');
        document.getElementById('appContainer').classList.remove('hidden');
        document.getElementById('userName').textContent = userData.name;
        document.getElementById('userAvatar').src = userData.avatar;
        showPage('dashboard');
        await refreshDashboard();
    } else {
        showNotification('Registration failed. Please try again.', 'error');
    }
}

async function handleGmailLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    // Try API login first
    const result = await fetchFromAPI('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });

    if (result && result.success) {
        currentUser = result.data;
        saveCurrentUser();
        
        showNotification('Login successful!', 'success');
        document.getElementById('loginPage').classList.remove('active');
        document.getElementById('appContainer').classList.remove('hidden');
        document.getElementById('userName').textContent = currentUser.name;
        document.getElementById('userAvatar').src = currentUser.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser.name)}&background=random`;
        showPage('dashboard');
        await refreshDashboard();
    } else {
        // Fallback to local storage
        if (users[email] && users[email].password === password) {
            currentUser = users[email];
            saveCurrentUser();
            
            showNotification('Login successful!', 'success');
            document.getElementById('loginPage').classList.remove('active');
            document.getElementById('appContainer').classList.remove('hidden');
            document.getElementById('userName').textContent = currentUser.name;
            document.getElementById('userAvatar').src = currentUser.avatar;
            showPage('dashboard');
            await refreshDashboard();
        } else {
            showNotification('Invalid email or password!', 'error');
        }
    }
}

function logout() {
    currentUser = null;
    localStorage.removeItem('mindcare_current_user');
    document.getElementById('appContainer').classList.add('hidden');
    document.getElementById('registrationPage').classList.add('active');
    showNotification('Logged out successfully', 'success');
}

// ==================== PAGE NAVIGATION ====================
function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Show selected page
    const selectedPage = document.getElementById(pageId + 'Page');
    if (selectedPage) {
        selectedPage.classList.add('active');
    }
    
    // Update nav active state
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('bg-purple-100', 'text-purple-700', 'dark:bg-purple-900', 'dark:text-purple-300');
        if (link.getAttribute('onclick').includes(pageId)) {
            link.classList.add('bg-purple-100', 'text-purple-700', 'dark:bg-purple-900', 'dark:text-purple-300');
        }
    });
    
    // Page-specific initialization
    if (pageId === 'dashboard') {
        refreshDashboard();
    } else if (pageId === 'progress') {
        loadProgress();
    } else if (pageId === 'profile') {
        loadProfile();
    }
}

// ==================== DASHBOARD FUNCTIONS ====================
// script.js — refreshDashboard() fix
async function refreshDashboard() {
  const user = JSON.parse(localStorage.getItem('mindcare_current_user'));
  if (!user?.id) return;

  // ✅ Correct endpoint
  const data = await fetch(
    `http://localhost:5000/api/user-history/${user.id}`
  ).then(r => r.json()).catch(() => null);

  if (!data?.assessments?.length) {
    // No assessments - show default state
    document.getElementById('dashboardScore').textContent = '--';
    document.getElementById('dashboardLabel').textContent = '--';
    document.getElementById('dashboardSummary').textContent = 'Take an assessment to get your wellness score';
    updateDashboardProgressRing(0);
    populateRecentActivitiesList([]);
    return;
  }

  const latest = data.assessments[0];   // already sorted desc
  const score  = latest.questionnaire?.score ?? 0;

  // Display the actual score (not percentage)
  document.getElementById('dashboardScore').textContent = score;

  // Determine status and summary like profile.html does
  let status = 'Excellent';
  let summary = 'Your mental health is in great shape! Keep up the great work.';
  
  if (score < 40) {
    status = 'Needs Attention';
    summary = 'Consider reaching out for professional support.';
  } else if (score < 60) {
    status = 'Fair';
    summary = 'Focus on self-care and stress management techniques.';
  } else if (score < 80) {
    status = 'Good';
    summary = 'You\'re doing well! Continue your positive habits.';
  }

  document.getElementById('dashboardLabel').textContent = status;
  document.getElementById('dashboardSummary').textContent = summary;

  // Update progress ring based on score (out of max score ~100)
  const percentScore = Math.min((score / 100) * 100, 100);
  updateDashboardProgressRing(percentScore);

  populateRecentActivitiesList(data.assessments.slice(0, 3));
}

// Function to update the dashboard progress ring
function updateDashboardProgressRing(percentage) {
  const circle = document.getElementById('dashboardProgressCircle');
  if (circle) {
    const circumference = 2 * Math.PI * 70; // r=70
    const offset = circumference - (percentage / 100) * circumference;
    circle.style.strokeDashoffset = offset;
  }
}
// Add helper called inside refreshDashboard()
function populateRecentActivitiesList(assessments) {
  const el = document.getElementById('recentActivitiesList');
  if (!el) return;

  if (!assessments.length) {
    el.innerHTML = '<p class="text-gray-400 text-sm">No assessments yet</p>';
    return;
  }

  el.innerHTML = assessments.map(a => {
    const risk  = a.final_result?.risk_level || 'Unknown';
    const score = a.questionnaire?.score ?? '--';
    const date  = new Date(a.timestamp).toLocaleDateString();
    const color = risk.includes('Low') ? 'green' :
                  risk.includes('Moderate') ? 'yellow' : 'red';
    return `<div class="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
      <div>
        <p class="text-sm font-medium text-gray-700">${risk}</p>
        <p class="text-xs text-gray-500">${date}</p>
      </div>
      <span class="text-sm font-bold text-${color}-600">Score: ${score}</span>
    </div>`;
  }).join('');
}
function updateDashboardScore() {
    if (!currentUser || !currentUser.surveyHistory || currentUser.surveyHistory.length === 0) {
        document.getElementById('currentScore').textContent = '--';
        document.getElementById('scoreLabel').textContent = 'No Data';
        document.getElementById('scoreLabel').className = 'text-sm text-gray-500';
        return;
    }

    const latest = currentUser.surveyHistory[currentUser.surveyHistory.length - 1];
    const score = latest.score;
    
    document.getElementById('currentScore').textContent = score;
    
    let label, labelClass;
    if (score >= 80) {
        label = 'Excellent';
        labelClass = 'text-sm text-green-600';
    } else if (score >= 60) {
        label = 'Good';
        labelClass = 'text-sm text-yellow-600';
    } else if (score >= 40) {
        label = 'Fair';
        labelClass = 'text-sm text-orange-600';
    } else {
        label = 'Needs Attention';
        labelClass = 'text-sm text-red-600';
    }
    
    document.getElementById('scoreLabel').textContent = label;
    document.getElementById('scoreLabel').className = labelClass;
}

function renderRecentActivities() {
    const container = document.getElementById('recentActivities');
    if (!container) return;
    
    if (!currentUser || !currentUser.surveyHistory || currentUser.surveyHistory.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No recent activities</p>';
        return;
    }

    const recent = currentUser.surveyHistory.slice(-3).reverse();
    let html = '';
    
    recent.forEach(activity => {
        const date = new Date(activity.date);
        const dateStr = date.toLocaleDateString();
        const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        html += `
            <div class="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="w-2 h-2 rounded-full ${
                    activity.score >= 80 ? 'bg-green-500' :
                    activity.score >= 60 ? 'bg-yellow-500' :
                    'bg-red-500'
                }"></div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
                        ${activity.status} Assessment
                    </p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">
                        ${dateStr} at ${timeStr}
                    </p>
                </div>
                <span class="text-sm font-bold ${
                    activity.score >= 80 ? 'text-green-600' :
                    activity.score >= 60 ? 'text-yellow-600' :
                    'text-red-600'
                }">
                    ${activity.score}
                </span>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function renderHistoryCards() {
    const historyContainer = document.getElementById('historyCards');
    if (!historyContainer) return;
    
    if (!currentUser || !currentUser.surveyHistory || currentUser.surveyHistory.length === 0) {
        historyContainer.innerHTML = `
            <div class="col-span-full text-center py-8">
                <i class="fas fa-clipboard-list text-4xl text-gray-300 mb-3"></i>
                <p class="text-gray-500">No assessment history yet</p>
                <button onclick="showPage('survey')" class="mt-3 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">
                    Take Your First Assessment
                </button>
            </div>
        `;
        return;
    }

    // Sort history by date (newest first)
    const sortedHistory = [...currentUser.surveyHistory].sort((a, b) => 
        new Date(b.date) - new Date(a.date)
    );

    // Generate HTML for history cards
    let html = '';
    sortedHistory.slice(0, 6).forEach(entry => {
        const date = new Date(entry.date);
        const dateStr = date.toLocaleDateString();
        const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Determine status color and icon
        let statusColor = 'text-gray-600';
        let statusBg = 'bg-gray-100';
        let statusIcon = 'fa-question-circle';
        
        if (entry.status === 'Low Risk') {
            statusColor = 'text-green-600';
            statusBg = 'bg-green-100';
            statusIcon = 'fa-check-circle';
        } else if (entry.status === 'Moderate Risk') {
            statusColor = 'text-yellow-600';
            statusBg = 'bg-yellow-100';
            statusIcon = 'fa-exclamation-circle';
        } else if (entry.status === 'High Risk') {
            statusColor = 'text-orange-600';
            statusBg = 'bg-orange-100';
            statusIcon = 'fa-exclamation-triangle';
        } else if (entry.status === 'Critical Risk') {
            statusColor = 'text-red-600';
            statusBg = 'bg-red-100';
            statusIcon = 'fa-times-circle';
        }

        html += `
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-md transition-shadow p-4 border border-gray-100 dark:border-gray-700">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex items-center">
                        <div class="w-10 h-10 rounded-full ${statusBg} flex items-center justify-center mr-3">
                            <i class="fas ${statusIcon} ${statusColor}"></i>
                        </div>
                        <div>
                            <p class="font-semibold text-gray-800 dark:text-white">${entry.status}</p>
                            <p class="text-xs text-gray-500 dark:text-gray-400">${dateStr} at ${timeStr}</p>
                        </div>
                    </div>
                    <span class="text-2xl font-bold ${entry.score >= 80 ? 'text-green-600' : entry.score >= 60 ? 'text-yellow-600' : 'text-red-600'}">
                        ${entry.score}
                    </span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div class="h-2 rounded-full transition-all duration-500 ${entry.score >= 80 ? 'bg-green-500' : entry.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}" 
                         style="width: ${entry.score}%"></div>
                </div>
                <button onclick="viewAssessmentDetails('${entry.assessmentId}')" 
                        class="mt-3 text-sm text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-300 font-medium">
                    View Details →
                </button>
            </div>
        `;
    });

    historyContainer.innerHTML = html;
}

// ==================== DAILY QUOTE FUNCTIONS ====================
async function fetchDailyQuote() {
    const quoteData = await fetchFromAPI('/daily-quote');
    
    if (quoteData && quoteData.success) {
        const quote = quoteData.data;
        displayQuote(quote.text, quote.author || 'Unknown');
    } else {
        // Fallback to local quotes if API fails
        displayDailyQuote();
    }
}

function displayDailyQuote() {
    const quotes = [
        { text: "The only way to do great work is to love what you do.", author: "Steve Jobs" },
        { text: "Believe you can and you're halfway there.", author: "Theodore Roosevelt" },
        { text: "Your limitation—it's only your imagination.", author: "Unknown" },
        { text: "Great things never come from comfort zones.", author: "Unknown" },
        { text: "Dream it. Wish it. Do it.", author: "Unknown" },
        { text: "Success doesn't just find you. You have to go out and get it.", author: "Unknown" },
        { text: "The harder you work for something, the greater you'll feel when you achieve it.", author: "Unknown" },
        { text: "Don't stop when you're tired. Stop when you're done.", author: "Unknown" },
        { text: "Wake up with determination. Go to bed with satisfaction.", author: "Unknown" },
        { text: "Do something today that your future self will thank you for.", author: "Sean Patrick Flanery" },
        { text: "Little things make big days.", author: "Unknown" },
        { text: "It's going to be hard, but hard does not mean impossible.", author: "Unknown" },
        { text: "Don't wait for opportunity. Create it.", author: "Unknown" },
        { text: "Sometimes we're tested not to show our weaknesses, but to discover our strengths.", author: "Unknown" },
        { text: "The key to success is to focus on goals, not obstacles.", author: "Unknown" }
    ];
    
    const today = new Date().toDateString();
    const savedQuote = localStorage.getItem('mindcare_daily_quote');
    
    if (savedQuote) {
        const { date, quote } = JSON.parse(savedQuote);
        if (date === today) {
            displayQuote(quote.text, quote.author);
            return;
        }
    }
    
    const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
    localStorage.setItem('mindcare_daily_quote', JSON.stringify({ date: today, quote: randomQuote }));
    displayQuote(randomQuote.text, randomQuote.author);
}

function displayQuote(text, author) {
    const quoteText = document.getElementById('dailyQuoteText');
    const quoteAuthor = document.getElementById('dailyQuoteAuthor');
    
    if (quoteText) quoteText.textContent = `"${text}"`;
    if (quoteAuthor) quoteAuthor.textContent = `— ${author}`;
}

// ==================== ACTIVITIES FUNCTIONS ====================
async function fetchActivities() {
    const activitiesData = await fetchFromAPI('/activities');
    
    if (activitiesData && activitiesData.success) {
        renderActivities(activitiesData.data);
    } else {
        // Fallback to local activities if API fails
        renderLocalActivities();
    }
}

function renderActivities(activities) {
    const activitiesContainer = document.getElementById('activitiesList');
    if (!activitiesContainer) return;
    
    if (!activities || activities.length === 0) {
        activitiesContainer.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-spa text-3xl text-gray-300 mb-2"></i>
                <p class="text-gray-500">No activities available</p>
            </div>
        `;
        return;
    }

    let html = '';
    activities.forEach(activity => {
        html += `
            <div class="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow">
                <div class="flex items-center mb-2">
                    <i class="${activity.icon || 'fa-star'} text-purple-500 mr-2"></i>
                    <h4 class="font-semibold text-gray-800 dark:text-white">${activity.title}</h4>
                </div>
                <p class="text-sm text-gray-600 dark:text-gray-300 mb-3">${activity.description}</p>
                <button onclick="openActivityModal('${activity._id || activity.type}')" 
                        class="text-sm text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-300 font-medium">
                    Start Activity →
                </button>
            </div>
        `;
    });
    
    activitiesContainer.innerHTML = html;
}

function renderLocalActivities() {
    const activities = [
        { title: 'Mindful Breathing', description: 'Take 5 minutes to focus on your breath', icon: 'fa-wind', type: 'mindfulness' },
        { title: 'Gratitude Journal', description: 'Write down 3 things you\'re grateful for', icon: 'fa-book', type: 'creative' },
        { title: 'Quick Stretch', description: 'Simple stretches to relieve tension', icon: 'fa-child', type: 'exercise' },
        { title: 'Connect with Friends', description: 'Reach out to someone you care about', icon: 'fa-users', type: 'social' },
        { title: 'Self-Care Time', description: 'Do something that makes you happy', icon: 'fa-heart', type: 'selfcare' },
        { title: 'Learn Something New', description: 'Expand your knowledge today', icon: 'fa-graduation-cap', type: 'learning' }
    ];
    
    renderActivities(activities);
}

// ==================== MODAL FUNCTIONS ====================
function openModal(activityType) {
    const modal = document.getElementById('activityModal');
    if (!modal) return;

    const titleEl = document.getElementById('modalTitle');
    const contentEl = document.getElementById('modalContent');
    if (contentEl) contentEl.innerHTML = '';

    let title = '', description = '', items = [];
    
    if (activityRecommendations[activityType]) {
        const activity = activityRecommendations[activityType];
        title = activity.title;
        description = activity.description;
        items = activity.items;
    } else {
        title = 'Activity Suggestions';
        description = 'Here are some activities you can try:';
        items = [];
    }

    // Set modal title and content
    if (titleEl) titleEl.textContent = title;
    if (contentEl) {
        contentEl.innerHTML = `
            <p class="text-gray-600 dark:text-gray-300 mb-4">${description}</p>
            <ul class="list-disc list-inside space-y-2">
                ${items.map(item => `<li class="text-gray-700 dark:text-gray-200">${item}</li>`).join('')}
            </ul>
            <div class="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button onclick="completeActivity('${activityType}')" 
                        class="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">
                    Mark as Complete
                </button>
            </div>
        `;
    }

    // Show modal
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    // ✅ Use display:flex instead of toggling 'hidden' class
  const openmodal = document.getElementById('activityModal');
  openmodal.style.display = 'flex';
  document.body.style.overflow = 'hidden';

}
function closeModal() {
    const modal = document.getElementById('activityModal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

async function completeActivity(activityId) {
    if (!currentUser || !currentUser.id) {
        showNotification('Please log in to complete activities', 'error');
        return;
    }
    
    const result = await fetchFromAPI('/complete-activity', {
        method: 'POST',
        body: JSON.stringify({
            user_id: currentUser.id,
            activity_id: activityId
        })
    });
    
    if (result && result.success) {
        showNotification('Activity completed successfully!', 'success');
        closeModal();
        // Refresh activities to show completion status
        await fetchActivities();
    } else {
        // Local completion tracking
        if (!currentUser.completedActivities) {
            currentUser.completedActivities = [];
        }
        currentUser.completedActivities.push({
            activityId,
            completedAt: new Date().toISOString()
        });
        saveCurrentUser();
        
        showNotification('Activity completed successfully!', 'success');
        closeModal();
    }
}

// ==================== ASSESSMENT FUNCTIONS ====================
function viewAssessmentDetails(assessmentId) {
    // Store the ID and open details modal
    localStorage.setItem('selectedAssessmentId', assessmentId);
    showPage('assessment-details');
    loadAssessmentDetails(assessmentId);
}

async function loadAssessmentDetails(assessmentId) {
    const detailsData = await fetchFromAPI(`/assessment/${assessmentId}`);
    
    if (detailsData && detailsData.success) {
        renderAssessmentDetails(detailsData.data);
    } else {
        // Fallback to local data
        if (currentUser && currentUser.surveyHistory) {
            const assessment = currentUser.surveyHistory.find(a => a.assessmentId === assessmentId);
            if (assessment) {
                renderLocalAssessmentDetails(assessment);
            }
        }
    }
}

function renderAssessmentDetails(assessment) {
    const container = document.getElementById('assessmentDetailsContainer');
    if (!container) return;
    
    const date = new Date(assessment.timestamp).toLocaleString();
    const riskLevel = assessment.final_result?.risk_level || 'Unknown';
    const riskScore = assessment.questionnaire_result?.risk_score || 0;
    
    container.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-gray-800 dark:text-white">Assessment Details</h2>
                <span class="px-3 py-1 rounded-full text-sm font-medium ${
                    riskLevel === 'Low Risk' ? 'bg-green-100 text-green-700' :
                    riskLevel === 'Moderate Risk' ? 'bg-yellow-100 text-yellow-700' :
                    riskLevel === 'High Risk' ? 'bg-orange-100 text-orange-700' :
                    'bg-red-100 text-red-700'
                }">
                    ${riskLevel}
                </span>
            </div>
            
            <div class="grid md:grid-cols-2 gap-6">
                <div>
                    <h3 class="font-semibold text-gray-700 dark:text-gray-300 mb-2">Date & Time</h3>
                    <p class="text-gray-600 dark:text-gray-400">${date}</p>
                </div>
                
                <div>
                    <h3 class="font-semibold text-gray-700 dark:text-gray-300 mb-2">Risk Score</h3>
                    <p class="text-3xl font-bold ${riskScore >= 80 ? 'text-green-600' : riskScore >= 60 ? 'text-yellow-600' : 'text-red-600'}">
                        ${riskScore}/100
                    </p>
                </div>
            </div>
            
            <div class="mt-6">
                <h3 class="font-semibold text-gray-700 dark:text-gray-300 mb-3">Recommendations</h3>
                <ul class="space-y-2">
                    ${assessment.final_result?.recommendations?.map(rec => 
                        `<li class="flex items-start">
                            <i class="fas fa-check-circle text-green-500 mt-1 mr-2"></i>
                            <span class="text-gray-600 dark:text-gray-400">${rec}</span>
                        </li>`
                    ).join('') || '<li class="text-gray-500">No recommendations available</li>'}
                </ul>
            </div>
            
            <div class="mt-6 flex gap-3">
                <button onclick="showPage('progress')" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">
                    View Progress
                </button>
                <button onclick="showPage('survey')" class="px-4 py-2 border border-purple-600 text-purple-600 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 transition">
                    Take New Assessment
                </button>
            </div>
        </div>
    `;
}

function renderLocalAssessmentDetails(assessment) {
    const container = document.getElementById('assessmentDetailsContainer');
    if (!container) return;
    
    const date = new Date(assessment.date).toLocaleString();
    
    container.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-gray-800 dark:text-white">Assessment Details</h2>
                <span class="px-3 py-1 rounded-full text-sm font-medium ${
                    assessment.score >= 80 ? 'bg-green-100 text-green-700' :
                    assessment.score >= 60 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                }">
                    ${assessment.status}
                </span>
            </div>
            
            <div class="grid md:grid-cols-2 gap-6">
                <div>
                    <h3 class="font-semibold text-gray-700 dark:text-gray-300 mb-2">Date & Time</h3>
                    <p class="text-gray-600 dark:text-gray-400">${date}</p>
                </div>
                
                <div>
                    <h3 class="font-semibold text-gray-700 dark:text-gray-300 mb-2">Score</h3>
                    <p class="text-3xl font-bold ${assessment.score >= 80 ? 'text-green-600' : assessment.score >= 60 ? 'text-yellow-600' : 'text-red-600'}">
                        ${assessment.score}/100
                    </p>
                </div>
            </div>
            
            <div class="mt-6 flex gap-3">
                <button onclick="showPage('progress')" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">
                    View Progress
                </button>
                <button onclick="showPage('survey')" class="px-4 py-2 border border-purple-600 text-purple-600 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 transition">
                    Take New Assessment
                </button>
            </div>
        </div>
    `;
}

// ==================== SURVEY FUNCTIONS ====================
async function submitSurvey(e) {
    e.preventDefault();
    
    if (!currentUser || !currentUser.id) {
        showNotification('Please log in to take the survey', 'error');
        return;
    }

    const formData = new FormData(e.target);
    const responses = {};
    
    // Collect all survey responses
    for (let [key, value] of formData.entries()) {
        responses[key] = parseInt(value);
    }
    
    // Calculate score
    const values = Object.values(responses);
    const totalScore = values.reduce((sum, val) => sum + val, 0);
    const maxScore = values.length * 5;
    const percentageScore = Math.round((totalScore / maxScore) * 100);
    
    // Determine risk level
    let riskLevel = 'Low Risk';
    if (percentageScore < 40) {
        riskLevel = 'Critical Risk';
    } else if (percentageScore < 60) {
        riskLevel = 'High Risk';
    } else if (percentageScore < 80) {
        riskLevel = 'Moderate Risk';
    }
    
    const surveyData = {
        user_id: currentUser.id,
        responses: responses,
        timestamp: new Date().toISOString()
    };
    
    // Submit to API
    const result = await fetchFromAPI('/submit-survey', {
        method: 'POST',
        body: JSON.stringify(surveyData)
    });
    
    if (result && result.success) {
        // Update local user data
        if (!currentUser.surveyHistory) {
            currentUser.surveyHistory = [];
        }
        
        currentUser.surveyHistory.push({
            date: new Date().toISOString(),
            score: percentageScore,
            status: riskLevel,
            assessmentId: result.data.assessment_id
        });
        
        currentUser.latestScore = percentageScore;
        saveCurrentUser();
        
        showNotification('Survey submitted successfully!', 'success');
        showPage('dashboard');
        await refreshDashboard();
    } else {
        showNotification('Failed to submit survey. Please try again.', 'error');
    }
}

// ==================== PROGRESS FUNCTIONS ====================
function loadProgress() {
    if (!currentUser) {
        showNotification('Please log in to view progress', 'error');
        return;
    }
    
    updateProgressDetails();
    initCharts();
}

function updateProgressDetails() {
    if (!currentUser || !currentUser.surveyHistory || currentUser.surveyHistory.length === 0) {
        document.getElementById('totalAssessments').textContent = '0';
        document.getElementById('averageScore').textContent = '--';
        document.getElementById('improvement').textContent = '--';
        document.getElementById('currentStreak').textContent = '0';
        return;
    }
    
    const history = currentUser.surveyHistory;
    const totalAssessments = history.length;
    const scores = history.map(h => h.score);
    const averageScore = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
    
    // Calculate improvement (compare first and last)
    let improvement = 0;
    if (totalAssessments > 1) {
        improvement = scores[scores.length - 1] - scores[0];
    }
    
    // Calculate streak (consecutive days with assessments)
    let streak = 0;
    const today = new Date().toDateString();
    const sortedDates = history.map(h => new Date(h.date).toDateString()).sort().reverse();
    
    for (let i = 0; i < sortedDates.length; i++) {
        const checkDate = new Date();
        checkDate.setDate(checkDate.getDate() - i);
        if (sortedDates.includes(checkDate.toDateString())) {
            streak++;
        } else {
            break;
        }
    }
    
    document.getElementById('totalAssessments').textContent = totalAssessments;
    document.getElementById('averageScore').textContent = averageScore;
    document.getElementById('improvement').textContent = improvement >= 0 ? `+${improvement}` : improvement;
    document.getElementById('currentStreak').textContent = streak;
}

function initCharts() {
    if (!currentUser || !currentUser.surveyHistory || currentUser.surveyHistory.length === 0) {
        // Destroy existing charts if any
        if (weeklyChart) { weeklyChart.destroy(); weeklyChart = null; }
        if (monthlyChart) { monthlyChart.destroy(); monthlyChart = null; }
        return;
    }

    const all = currentUser.surveyHistory.map(s => ({ date: new Date(s.date), score: s.score }));
    all.sort((a, b) => a.date - b.date);

    // Weekly: last 7 entries
    const last7 = all.slice(-7);
    const weeklyLabels = last7.map(i => i.date.toLocaleDateString());
    const weeklyScores = last7.map(i => i.score);

    // Monthly: last 30 entries
    const last30 = all.slice(-30);
    const monthlyLabels = last30.map(i => i.date.toLocaleDateString());
    const monthlyScores = last30.map(i => i.score);

    // Destroy old charts
    if (weeklyChart) weeklyChart.destroy();
    if (monthlyChart) monthlyChart.destroy();

    // Create weekly chart
    const wCtx = document.getElementById('weeklyChart');
    if (wCtx) {
        weeklyChart = new Chart(wCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: weeklyLabels,
                datasets: [{
                    label: 'Score',
                    data: weeklyScores,
                    borderColor: 'rgb(147, 51, 234)',
                    backgroundColor: 'rgba(147, 51, 234, 0.1)',
                    borderWidth: 3,
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true, max: 100 }
                }
            }
        });
    }

    // Create monthly chart
    const mCtx = document.getElementById('monthlyChart');
    if (mCtx) {
        monthlyChart = new Chart(mCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: monthlyLabels,
                datasets: [{
                    label: 'Score',
                    data: monthlyScores,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.25,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true, max: 100 }
                }
            }
        });
    }
}

// ==================== PROFILE FUNCTIONS ====================
function loadProfile() {
    if (!currentUser) {
        showNotification('Please log in to view your profile', 'error');
        return;
    }

    // Update profile header
    document.getElementById('profileName').innerText = currentUser.name || 'User';
    document.getElementById('profileEmail').innerText = currentUser.email;
    document.getElementById('profileCollege').innerText = currentUser.college || 'Not Provided';
    document.getElementById('profilePhoto').src = currentUser.avatar || 'https://via.placeholder.com/120';

    // Mental Health Status
    const score = currentUser.latestScore || 0;
    document.getElementById('mhScore').innerText = score ? score + '/100' : '--';

    let label = '--';
    if (score >= 80) label = 'Healthy';
    else if (score >= 60) label = 'Moderate';
    else if (score > 0) label = 'Needs Attention';

    document.getElementById('mhLabel').innerText = label;

    const summaries = {
        Healthy: "You're doing great! Keep maintaining your positive habits.",
        Moderate: "You're stable, but could benefit from more consistent routines.",
        'Needs Attention': "You're under stress. Try mindfulness or talk to someone you trust.",
        '--': 'Take a survey to get started.'
    };

    document.getElementById('mhSummary').innerText = summaries[label] || summaries['--'];

    // Survey History
    const tbody = document.getElementById('historyTable');
    tbody.innerHTML = '';
    if (currentUser.surveyHistory && currentUser.surveyHistory.length > 0) {
        currentUser.surveyHistory.forEach(entry => {
            const statusLabel = entry.score >= 80 ? 'Healthy' : entry.score >= 60 ? 'Moderate' : 'Needs Attention';
            const statusColor = entry.score >= 80 ? 'text-green-600' : entry.score >= 60 ? 'text-yellow-600' : 'text-red-600';
            tbody.innerHTML += `
                <tr class="hover:bg-gray-50 transition">
                    <td class="p-3 text-gray-700">${new Date(entry.date).toLocaleDateString()}</td>
                    <td class="p-3 font-semibold text-gray-800">${entry.score}</td>
                    <td class="p-3"><span class="px-3 py-1 rounded-full text-sm font-medium ${statusColor === 'text-green-600' ? 'bg-green-100 text-green-700' : statusColor === 'text-yellow-600' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}">${statusLabel}</span></td>
                </tr>`;
        });
    } else {
        tbody.innerHTML = '<tr><td colspan="3" class="p-3 text-center text-gray-500">No survey data yet. Take a survey to get started.</td></tr>';
    }

    // Trends
    if (currentUser.surveyHistory && currentUser.surveyHistory.length > 0) {
        const scores = currentUser.surveyHistory.map(s => s.score);
        const avg = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
        const max = Math.max(...scores);
        const min = Math.min(...scores);
        const improve = scores.length > 1 ? scores[scores.length - 1] - scores[0] : 0;

        document.getElementById('avgScore').innerText = avg;
        document.getElementById('bestScore').innerText = max;
        document.getElementById('lowScore').innerText = min;
        document.getElementById('improveScore').innerText = (improve >= 0 ? '+' : '') + improve;
    } else {
        document.getElementById('avgScore').innerText = '--';
        document.getElementById('bestScore').innerText = '--';
        document.getElementById('lowScore').innerText = '--';
        document.getElementById('improveScore').innerText = '--';
    }
}

function openPhotoUpload() {
    document.getElementById('photoUpload').click();
}

function updatePhoto(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = e => {
        document.getElementById('profilePhoto').src = e.target.result;
        if (currentUser) {
            currentUser.avatar = e.target.result;
            users[currentUser.email] = currentUser;
            saveUsers();
            saveCurrentUser();
            document.getElementById('userAvatar').src = e.target.result;
            showNotification('Profile photo updated', 'success');
        }
    };
    reader.readAsDataURL(file);
}

function resetPassword() {
    const email = prompt('Enter your email for password reset:');
    if (!email) return;
    if (users[email]) {
        showNotification(`Password reset link sent to ${email}`, 'success');
    } else {
        showNotification('Email not found', 'error');
    }
}

// ==================== UTILITY FUNCTIONS ====================
function toggleProfileMenu() {
    const menu = document.getElementById('profileMenu');
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

function generateAIAffirmation() {
    if (!currentUser || !currentUser.surveyHistory || currentUser.surveyHistory.length === 0) {
        return "You're taking steps by checking in — that's progress. Keep going!";
    }
    const latest = currentUser.surveyHistory[currentUser.surveyHistory.length - 1];
    if (latest.score >= 80) return "Great work! Keep your positive routines and celebrate small wins.";
    if (latest.score >= 60) return "You're doing well. Try adding one small self-care routine today.";
    return "Be kind to yourself — small steps are still progress. Reach out if you need support.";
}

function renderAffirmationBox() {
    const box = document.getElementById('affirmationBox');
    if (box) {
        box.textContent = generateAIAffirmation();
    }
}

// ==================== EVENT LISTENERS ====================
document.addEventListener('DOMContentLoaded', () => {
    // Load users from localStorage
    loadUsers();
    
    // Wire up slider value displays
    document.querySelectorAll('.slider').forEach(sl => {
        sl.addEventListener('input', function() {
            const id = this.id + 'Value';
            const el = document.getElementById(id);
            if (el) el.textContent = this.value;
        });
    });

    // Password strength checker
    const pwd = document.getElementById('regPassword');
    if (pwd) {
        pwd.addEventListener('input', () => {
            const val = pwd.value;
            let strength = 0;
            if (val.length >= 8) strength++;
            if (/[a-z]/.test(val)) strength++;
            if (/[A-Z]/.test(val)) strength++;
            if (/[0-9]/.test(val)) strength++;
            if (/[$@#&!]/.test(val)) strength++;
            const bar = document.getElementById('passwordStrengthBar');
            const text = document.getElementById('passwordStrengthText');
            if (bar) bar.style.width = `${(strength/5)*100}%`;
            if (text) {
                if (strength <= 2) { text.textContent = 'Weak'; text.className = 'font-medium text-red-500'; }
                else if (strength <= 3) { text.textContent = 'Medium'; text.className = 'font-medium text-yellow-500'; }
                else { text.textContent = 'Strong'; text.className = 'font-medium text-green-500'; }
            }
        });
    }

    // Bind forms
    const regForm = document.getElementById('registrationForm');
    if (regForm) regForm.addEventListener('submit', handleRegistration);

    const loginForm = document.getElementById('gmailLoginForm');
    if (loginForm) loginForm.addEventListener('submit', handleGmailLogin);

    const surveyForm = document.getElementById('surveyForm');
    if (surveyForm) surveyForm.addEventListener('submit', submitSurvey);

    // Check for saved user
    const saved = localStorage.getItem('mindcare_current_user');
    if (saved) {
        try {
            currentUser = JSON.parse(saved);
            document.getElementById('appContainer').classList.remove('hidden');
            document.getElementById('registrationPage').classList.remove('active');
            document.getElementById('loginPage').classList.remove('active');
            document.getElementById('userName').textContent = currentUser.name || 'User';
            document.getElementById('userAvatar').src = currentUser.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser.name)}&background=random`;
            showPage('dashboard');
            refreshDashboard();
        } catch(e) {
            localStorage.removeItem('mindcare_current_user');
        }
    } else {
        document.getElementById('registrationPage').classList.add('active');
    }

    // Initialize quote display
    displayDailyQuote();

    // Handle hero image error
    const heroSection = document.querySelector('.dashboard-hero-section');
    if (heroSection) {
        const img = new Image();
        img.onerror = function() {
            heroSection.style.backgroundImage = '';
            heroSection.classList.add('bg-gradient-to-br', 'from-purple-600', 'via-blue-600', 'to-indigo-700');
            showNotification('Background image not found. Using a gradient instead.', 'warning');
        };
        img.src = 'assets/psychology-illustration.jpg';
    }

    // Close modals on outside click
    document.getElementById('activityModal')?.addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });

    // Close profile menu on outside click
    document.addEventListener('click', function(event) {
        const profileMenu = document.getElementById('profileMenu');
        const profileButton = event.target.closest('button');
        
        if (!profileButton || !profileButton.onclick || !profileButton.onclick.toString().includes('toggleProfileMenu')) {
            if (profileMenu) profileMenu.classList.add('hidden');
        }
    });

    // Set up periodic refresh (every 5 minutes)
    setInterval(() => {
        if (currentUser && document.getElementById('dashboardPage')?.classList.contains('active')) {
            refreshDashboard();
        }
    }, 300000);
});

// ==================== GLOBAL FUNCTIONS ====================
// Make functions globally accessible
window.showPage = showPage;
window.logout = logout;
window.toggleProfileMenu = toggleProfileMenu;
window.openModal = openModal;
window.closeModal = closeModal;
window.viewAssessmentDetails = viewAssessmentDetails;
window.completeActivity = completeActivity;
window.openPhotoUpload = openPhotoUpload;
window.updatePhoto = updatePhoto;
window.resetPassword = resetPassword;
window.refreshDashboard = refreshDashboard;
window.loadProfile = loadProfile;
window.loadProgress = loadProgress;