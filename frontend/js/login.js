document.addEventListener('DOMContentLoaded', () => {
    window.authHelpers.redirectToAppIfLogged();

    const form = document.getElementById('login-form');
    const errorEl = document.getElementById('login-error');

    if (!form) return;

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        errorEl.innerText = '';

        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        if (!username || !password) {
            errorEl.innerText = 'Informe usuário e senha.';
            return;
        }

        try {
            const response = await fetch(`${window.authHelpers.API_BASE_URL}/api/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({ username, password })
            });

            if (!response.ok) {
                const data = await response.json().catch(() => null);
                errorEl.innerText = data?.detail || 'Usuário ou senha inválidos';
                return;
            }

            const data = await response.json();
            window.authHelpers.setAccessToken(data.access_token);
            window.location.href = '/index.html';
        } catch (error) {
            console.error('Erro no login', error);
            errorEl.innerText = 'Erro ao conectar com a API.';
        }
    });
});
