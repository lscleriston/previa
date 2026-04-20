function handleLogin(event) {
    event.preventDefault();
    const errorEl = document.getElementById('login-error');
    errorEl.innerText = '';

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    if (!username || !password) {
        errorEl.innerText = 'Informe usuário e senha.';
        return false;
    }

    loginSubmit(username, password);
    return false;
}

async function loginSubmit(username, password) {
    const button = document.getElementById('login-button');
    const errorEl = document.getElementById('login-error');
    button.disabled = true;
    button.textContent = 'Entrando...';

    try {
        console.log('Tentando login para', username);
        const response = await fetch(`${window.authHelpers.API_BASE_URL}/api/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({ username, password })
        });

        console.log('Resposta do token:', response.status);

        if (!response.ok) {
            const data = await response.json().catch(() => null);
            errorEl.innerText = data?.detail || 'Usuário ou senha inválidos';
            return;
        }

        const data = await response.json();
        console.log('Token recebido:', data);
        window.authHelpers.setAccessToken(data.access_token);
        window.location.href = '/index.html';
    } catch (error) {
        console.error('Erro no login', error);
        errorEl.innerText = 'Erro ao conectar com a API.';
    } finally {
        button.disabled = false;
        button.textContent = 'Entrar';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.authHelpers.redirectToAppIfLogged();

    const form = document.getElementById('login-form');
    if (!form) return;
    form.addEventListener('submit', handleLogin);
});
