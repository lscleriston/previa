## Plano: Funcionalidade de Login e Gerenciamento de Usuários

**Resumo:** O objetivo é criar um sistema completo de autenticação e autorização, com uma tela de login, uma área administrativa para gerenciar usuários e as devidas alterações no banco de dados e backend para suportar tudo isso. Uma nova branch no Git será criada para isolar o desenvolvimento.

**Passos de Implementação:**

1.  **Criação da Branch:**
    *   Criar uma nova branch no Git chamada `feature/login` para isolar o desenvolvimento desta funcionalidade. (Concluído)

2.  **Banco de Dados (SQLite):**
    *   Criar uma nova tabela `users` para armazenar as informações dos usuários usando o script `backend/etl/etl_create_users_table.py`.
    *   **Estrutura da Tabela `users`:**
        *   `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
        *   `username` (TEXT, UNIQUE, NOT NULL)
        *   `password_hash` (TEXT, NOT NULL)
        *   `is_admin` (INTEGER, NOT NULL, DEFAULT 0)
        *   `created_at` (TEXT, NOT NULL)

3.  **Backend (FastAPI):**
    *   **Autenticação:**
        *   Integrar JWT (JSON Web Tokens) para gerenciar sessões de usuário.
        *   Criar um endpoint `/token` para o login, que validará as credenciais e retornará um token de acesso.
        *   Implementar um sistema de hashing de senhas (ex: `passlib`).
        *   Criar uma dependência (`Depends`) para proteger rotas que exigem autenticação.
    *   **API de Gerenciamento de Usuários (Acesso restrito a administradores):**
        *   `POST /api/users`: Criar um novo usuário.
        *   `GET /api/users`: Listar todos os usuários.
        *   `PUT /api/users/{user_id}`: Atualizar dados e permissões de um usuário.
        *   `DELETE /api/users/{user_id}`: Excluir um usuário.

4.  **Frontend:**
    *   **Tela de Login:**
        *   Criar `frontend/pages/login.html` com um formulário para `username` e `password`.
        *   Criar `frontend/js/login.js` para enviar as credenciais ao backend, receber o token e armazená-lo (ex: em `localStorage`).
        *   Implementar lógica para redirecionar usuários não autenticados para a tela de login.
    *   **Tela de Gerenciamento de Usuários (Acesso restrito a administradores):**
        *   Criar uma nova página (ex: `frontend/pages/admin_users.html`).
        *   Desenvolver a interface para listar, criar, editar e excluir usuários, consumindo a API do backend.

**Verificação:**

1.  **Testes Manuais:**
    *   Tentar acessar uma página protegida sem login e verificar o redirecionamento.
    *   Fazer login com um usuário comum e verificar se o acesso às páginas de admin é bloqueado.
    *   Fazer login como admin e testar todas as funcionalidades de CRUD de usuários.
    *   Verificar se a senha armazenada no banco de dados está em formato hash.
2.  **Testes Automatizados:**
    *   Adicionar testes de API para os novos endpoints de login e gerenciamento de usuários.

**Decisões:**

*   Usaremos JWT para autenticação por ser um padrão moderno e seguro para APIs.
*   As senhas serão armazenadas com hash para garantir a segurança.
*   O gerenciamento de usuários será restrito a usuários com a flag `is_admin`.
