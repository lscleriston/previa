const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8001'
    : 'http://backend:8000';

function getAccessToken() {
    return localStorage.getItem('access_token');
}

function setAccessToken(token) {
    localStorage.setItem('access_token', token);
}

function clearAccessToken() {
    localStorage.removeItem('access_token');
}

function getAuthHeaders() {
    const token = getAccessToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

function redirectToLoginIfNeeded() {
    const token = getAccessToken();
    if (!token && !window.location.pathname.endsWith('/login.html')) {
        window.location.href = '/login.html';
    }
}

function redirectToAppIfLogged() {
    if (getAccessToken() && window.location.pathname.endsWith('/login.html')) {
        window.location.href = '/index.html';
    }
}

async function fetchWithAuth(path, options = {}) {
    options.headers = {
        ...(options.headers || {}),
        ...getAuthHeaders(),
    };
    const response = await fetch(`${API_BASE_URL}${path}`, options);
    if (response.status === 401 || response.status === 403) {
        clearAccessToken();
        if (!window.location.pathname.endsWith('/login.html')) {
            window.location.href = '/login.html';
        }
    }
    return response;
}

async function getCurrentUser() {
    const response = await fetchWithAuth('/api/users/me');
    if (!response.ok) {
        throw new Error('Não foi possível obter usuário atual');
    }
    return response.json();
}

function logout() {
    clearAccessToken();
    window.location.href = '/login.html';
}

window.authHelpers = {
    API_BASE_URL,
    getAccessToken,
    setAccessToken,
    clearAccessToken,
    getAuthHeaders,
    fetchWithAuth,
    getCurrentUser,
    redirectToLoginIfNeeded,
    redirectToAppIfLogged,
    logout,
};

if (window.location.pathname.endsWith('/login.html')) {
    redirectToAppIfLogged();
} else {
    redirectToLoginIfNeeded();
}
