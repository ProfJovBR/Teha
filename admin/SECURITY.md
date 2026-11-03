# Administração exclusiva do proprietário

A API aceita somente o UUID 0fd8e9a2-88e5-4c08-ab8f-a5635db8c3ee com e-mail atual confirmado wcsam@outlook.com, validado pelo serviço Auth via getUser a cada requisição, e ainda exige presença em teha_admins. user_metadata e parâmetros do navegador nunca concedem privilégios.

O banco impõe uma constraint que impede qualquer outro UUID em teha_admins. Usuários anon/authenticated não podem inserir, atualizar ou remover administradores nem ler/escrever a auditoria administrativa diretamente. Registros clínicos e seu histórico continuam isolados pelo proprietário via RLS. O histórico clínico não pode ser alterado ou apagado pelo cliente. A API protege o e-mail proprietário contra alterações no próprio painel.

Testes: nove cenários da API (anônimo, usuário comum, origem externa, identidade e e-mail divergentes, proteção do proprietário e auditoria sem credenciais) passaram. Verificações transacionais no Postgres confirmaram escrita autorizada, isolamento entre contas, bloqueio de promoção a administrador, bloqueio de leitura da auditoria administrativa e bloqueio de exclusão de histórico.

Limites: isso não é garantia de ausência de vulnerabilidades ou pentest independente. Quem controla a conta Supabase/projeto ou obtém uma chave de servidor pode ultrapassar RLS. Ative MFA no Supabase e proteja as credenciais. A proteção contra senhas já vazadas do Supabase está desativada e exige plano Pro ou superior; nenhuma compra ou alteração de plano foi feita. O painel ainda não exige um segundo fator próprio. Alterações de senha não prometem revogação imediata de todos os JWT previamente emitidos.
