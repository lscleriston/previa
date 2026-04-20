document.addEventListener('DOMContentLoaded', async () => {
    window.authHelpers.redirectToLoginIfNeeded();

    const statusEl = document.getElementById('status-message');
    const usersTable = document.getElementById('users-table-body');
    const form = document.getElementById('create-user-form');
    const submitButton = document.getElementById('create-user-button');
    const usernameInput = document.getElementById('new-username');
    const passwordInput = document.getElementById('new-password');
    const isAdminCheckbox = document.getElementById('new-is-admin');

    let editMode = false;
    let editUserId = null;

    async function showStatus(message, type = 'info') {
        if (!statusEl) return;
        statusEl.innerText = message;
        statusEl.className = type === 'error' ? 'status-error' : 'status-success';
    }

    async function loadUsers() {
        try {
            const response = await window.authHelpers.fetchWithAuth('/api/users');
            if (!response.ok) {
                throw new Error('Falha ao buscar usuários');
            }
            const users = await response.json();
            renderUsers(users);
        } catch (error) {
            console.error(error);
            showStatus('Erro ao carregar usuários.', 'error');
        }
    }

    function renderUsers(users) {
        if (!usersTable) return;
        usersTable.innerHTML = '';

        if (!Array.isArray(users) || users.length === 0) {
            usersTable.innerHTML = '<tr><td colspan="4">Nenhum usuário encontrado.</td></tr>';
            return;
        }

        users.forEach((user) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.is_admin ? 'Sim' : 'Não'}</td>
                <td>
                    <button class="btn-sm" onclick="window.adminUsers.editUser(${user.id}, '${user.username.replace(/'/g, "\\'")}', ${user.is_admin})">Editar</button>
                    <button class="btn-sm btn-danger" onclick="window.adminUsers.deleteUser(${user.id})">Excluir</button>
                </td>
            `;
            usersTable.appendChild(row);
        });
    }

    async function createUser(event) {
        event.preventDefault();
        submitButton.disabled = true;
        const username = usernameInput.value.trim();
        const password = passwordInput.value;
        const isAdmin = isAdminCheckbox.checked;

        if (!username || !password) {
            showStatus('Informe usuário e senha.', 'error');
            submitButton.disabled = false;
            return;
        }

        try {
            const endpoint = editMode ? `/api/users/${editUserId}` : '/api/users';
            const method = editMode ? 'PUT' : 'POST';
            const payload = {
                username,
                is_admin: isAdmin,
            };
            if (password) payload.password = password;

            const response = await window.authHelpers.fetchWithAuth(endpoint, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                throw new Error(errorData?.detail || 'Erro ao salvar usuário');
            }

            await loadUsers();
            resetForm();
            showStatus(editMode ? 'Usuário atualizado com sucesso.' : 'Usuário criado com sucesso.', 'success');
        } catch (error) {
            console.error(error);
            showStatus(error.message, 'error');
        } finally {
            submitButton.disabled = false;
        }
    }

    function resetForm() {
        editMode = false;
        editUserId = null;
        usernameInput.value = '';
        passwordInput.value = '';
        isAdminCheckbox.checked = false;
        document.getElementById('form-title').innerText = 'Criar novo usuário';
        submitButton.innerText = 'Criar usuário';
    }

    async function deleteUser(userId) {
        if (!confirm('Tem certeza que deseja excluir este usuário?')) return;
        try {
            const response = await window.authHelpers.fetchWithAuth(`/api/users/${userId}`, { method: 'DELETE' });
            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                throw new Error(errorData?.detail || 'Erro ao excluir usuário');
            }
            showStatus('Usuário excluído com sucesso.', 'success');
            await loadUsers();
        } catch (error) {
            console.error(error);
            showStatus(error.message, 'error');
        }
    }

    function editUser(userId, username, isAdmin) {
        editMode = true;
        editUserId = userId;
        usernameInput.value = username;
        passwordInput.value = '';
        isAdminCheckbox.checked = isAdmin;
        document.getElementById('form-title').innerText = `Editando usuário ${username}`;
        submitButton.innerText = 'Salvar alterações';
    }

    window.adminUsers = {
        deleteUser,
        editUser,
    };

    if (form) {
        form.addEventListener('submit', createUser);
    }

    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', (event) => {
            event.preventDefault();
            window.authHelpers.logout();
        });
    }

    await loadUsers();
});
