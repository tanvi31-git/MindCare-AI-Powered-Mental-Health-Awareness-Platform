// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// User Management
let currentUser = null;
let users = {};

// Initialize users from localStorage
function loadUsers() {
    const savedUsers = localStorage.getItem('mindcare_users');
    if (savedUsers) {
        try {
            users = JSON.parse(savedUsers);
        } catch (e) {
            console.error('Error loading users:', e);
            users = {};
        }
    }
}

// Save users to localStorage
function saveUsers() {
    localStorage.setItem('mindcare_users', JSON.stringify(users));
}

// Save current user to localStorage
function saveCurrentUser() {
    if (currentUser) {
        localStorage.setItem('mindcare_current_user', JSON.stringify(currentUser));
        // Update UI elements if they exist (only on dashboard)
        const userNameEl = document.getElementById('userName');
        const userAvatarEl = document.getElementById('userAvatar');
        
        if (userNameEl) userNameEl.textContent = currentUser.name || 'User';
        if (userAvatarEl) userAvatarEl.src = currentUser.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser.name)}&background=random`;
    }
}

// Show notification on registration page
function showNotification(message, type = 'info') {
    const loginStatus = document.getElementById('loginStatus');
    const registrationStatus = document.getElementById('registrationStatus');
    
    if (loginStatus) {
        document.getElementById('loginStatusText').textContent = message;
        loginStatus.className = 'mb-4 p-3 rounded-lg text-sm text-center ' + 
            (type === 'success' ? 'bg-green-100 text-green-700' : 
             type === 'error' ? 'bg-red-100 text-red-700' : 
             type === 'warning' ? 'bg-yellow-100 text-yellow-700' : 
             'bg-blue-100 text-blue-700');
        loginStatus.classList.remove('hidden');
        setTimeout(() => loginStatus.classList.add('hidden'), 4000);
    }
    
    if (registrationStatus) {
        document.getElementById('registrationStatusText').textContent = message;
        registrationStatus.className = 'mb-4 p-3 rounded-lg text-sm text-center ' + 
            (type === 'success' ? 'bg-green-100 text-green-700' : 
             type === 'error' ? 'bg-red-100 text-red-700' : 
             type === 'warning' ? 'bg-yellow-100 text-yellow-700' : 
             'bg-blue-100 text-blue-700');
        registrationStatus.classList.remove('hidden');
        setTimeout(() => registrationStatus.classList.add('hidden'), 4000);
    }
    
    // Also log to console
    console.log(`[${type.toUpperCase()}] ${message}`);
}

async function handleGmailLogin(event) {
    event.preventDefault();
    
    const emailEl = document.getElementById('gmail');
    const passwordEl = document.getElementById('password');
    
    if (!emailEl || !passwordEl) {
        showNotification('Login form not found', 'error');
        return;
    }
    
    const email = emailEl.value.trim();
    const password = passwordEl.value;

    if (!email || !password) {
        showNotification('Please enter both email and password', 'error');
        return;
    }

    try {
        showNotification('Logging in...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const result = await response.json();

        if (result.success && result.user) {
            currentUser = result.user;
            saveCurrentUser();
            showNotification('Login successful! Redirecting...', 'success');
            
            // Clear form
            emailEl.value = '';
            passwordEl.value = '';
            
            // Redirect after short delay
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
        } else {
            showNotification(result.error || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Handle registration
async function handleRegistration(event) {
    event.preventDefault();
    
    const nameEl = document.getElementById('regName');
    const emailEl = document.getElementById('regGmail');
    const passwordEl = document.getElementById('regPassword');
    const confirmPasswordEl = document.getElementById('regConfirmPassword');
    
    if (!nameEl || !emailEl || !passwordEl || !confirmPasswordEl) {
        showNotification('Registration form not found', 'error');
        return;
    }
    
    const name = nameEl.value.trim();
    const email = emailEl.value.trim();
    const password = passwordEl.value;
    const confirmPassword = confirmPasswordEl.value;

    if (!name || !email || !password || !confirmPassword) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    if (password !== confirmPassword) {
        showNotification('Passwords do not match', 'error');
        return;
    }

    if (password.length < 6) {
        showNotification('Password must be at least 6 characters', 'error');
        return;
    }

    try {
        showNotification('Creating account...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });

        const result = await response.json();

        if (result.success && result.user) {
            showNotification('Account created successfully! Switching to login...', 'success');
            
            // Clear form
            nameEl.value = '';
            emailEl.value = '';
            passwordEl.value = '';
            confirmPasswordEl.value = '';
            
            // Switch to login page after delay
            setTimeout(() => {
                showLoginPage();
                showNotification('Please login with your new account', 'info');
            }, 1500);
        } else {
            showNotification(result.error || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('Network error: ' + error.message, 'error');
    }
}


// Logout function
function logout() {
    currentUser = null;
    localStorage.removeItem('mindcare_current_user');
    
    const appContainer = document.getElementById('appContainer');
    const registrationPage = document.getElementById('registrationPage');
    
    if (appContainer) appContainer.classList.add('hidden');
    if (registrationPage) registrationPage.classList.remove('hidden');
    
    showNotification('Logged out successfully', 'success');
    
    // Redirect to registration page
    setTimeout(() => {
        window.location.href = 'registration.html';
    }, 1000);
}

// Show page function
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

    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    const activeNav = document.querySelector(`[onclick="showPage('${pageId}')"]`);
    if (activeNav) {
        activeNav.classList.add('active');
    }

    // Special handling for specific pages
    if (typeof refreshDashboard === 'function' && pageId === 'dashboard') {
        refreshDashboard();
    } else if (typeof loadSurvey === 'function' && pageId === 'survey') {
        loadSurvey();
    } else if (typeof loadProgress === 'function' && pageId === 'progress') {
        loadProgress();
    } else if (typeof loadProfile === 'function' && pageId === 'profile') {
        loadProfile();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    
    // Check if we're on registration page
    const isRegistrationPage = document.getElementById('registrationPage') !== null;
    
    // Check for saved user
    const saved = localStorage.getItem('mindcare_current_user');
    if (saved) {
        try {
            currentUser = JSON.parse(saved);
            if (isRegistrationPage) {
                // Already on registration page, redirect to dashboard
                window.location.href = 'index.html';
            }
        } catch(e) {
            console.error('Session corrupted:', e);
            localStorage.removeItem('mindcare_current_user');
        }
    } else if (!isRegistrationPage) {
        // On dashboard but not logged in, redirect to login
        window.location.href = 'registration.html';
    } else {
        // On registration page and not logged in - show login form
        const loginPage = document.getElementById('loginPage');
        if (loginPage) {
            loginPage.classList.add('active');
            loginPage.classList.remove('hidden');
        }
    }
});
