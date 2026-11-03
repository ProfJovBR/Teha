# Teha Administração

Projeto independente do cliente clínico, com pacote/build e publicação próprios em https://teha-admin.pages.dev. O código fica no diretório admin/ do repositório ProfJovBR/Teha. Usa o banco Clinica para gerenciar contas desse projeto Supabase; não altera contas de outros projetos.

## Funcionalidades

- Login exclusivo para administradores autorizados.
- Lista de contas paginada, busca na página e último login bem-sucedido (auth.users.last_sign_in_at).
- Criação de contas com e-mail já confirmado e senha definida pelo administrador.
- Alteração de e-mail e redefinição de senha.
- Histórico de operações administrativas com horário, responsável, alvo e resultado. Não armazena senhas, tokens nem o corpo das solicitações.

O horário é exibido em America/Sao_Paulo. Último login não é presença online nem última atividade. Alterar senha bloqueia a senha anterior em novos logins; este painel não promete invalidar imediatamente todos os JWT já emitidos.

## Estado de ativação

O painel e a API estão ativos. Administração exclusiva da conta confirmada `wcsam@outlook.com`, vinculada ao UUID aprovado. O banco limita a lista de administradores a esse UUID; a API exige também o e-mail atual validado no Auth. O e-mail proprietário não pode ser substituído pelo painel. Veja [proteções, testes e limites](SECURITY.md).

## Segurança e implantação

A Edge Function valida o JWT com getUser a cada solicitação e consulta a allowlist no banco. verify_jwt do gateway é false porque a função implementa a autenticação diretamente, inclusive com chaves publicáveis modernas; isso não permite acesso anônimo. O cliente usa apenas SUPABASE_PUBLISHABLE_KEY. SUPABASE_SERVICE_ROLE_KEY é lida exclusivamente no ambiente da função, nunca no bundle ou no Git.

CORS aceita somente https://teha-admin.pages.dev. RLS impede que usuários comuns leiam a auditoria administrativa ou concedam acesso. Não há cadastro público no painel; o cadastro público do site clínico não foi alterado nesta tarefa.

Para desenvolver: npm ci, configure SUPABASE_URL e SUPABASE_PUBLISHABLE_KEY, execute npm run build e npm test. Publicação Cloudflare Pages: raiz admin, saída dist, comando npm ci && npm run build. Edge Function: server/index.ts e server/handler.mjs.

Testes automatizados verificam rejeição de chamadas anônimas, usuários comuns e origens externas, payload de listagem sem metadados privados, senhas curtas e auditoria sem credenciais. Operações reais de criação/troca de senha não foram executadas: dependem da autorização do primeiro administrador.
