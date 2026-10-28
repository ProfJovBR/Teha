# Instruções para Codex — Teha

## Projeto
Teha é um painel administrativo para centros odontológicos. Trabalham neste repositório dois desenvolvedores, cada um com seu próprio Codex.

## Branches
- `main`: branch de integração. Não realizar desenvolvimento diretamente nela; usar Pull Requests revisados.
- `frontend`: interface do usuário, acessibilidade, telas, componentes, integrações de cliente.
- `backend`: API, serviços, banco de dados, migrações, autenticação, autorização e integrações externas.
- Trabalhar somente na branch atribuída, salvo autorização explícita.
- Antes de modificar contratos compartilhados (endpoints, schemas, tipos), documentar a mudança e coordenar com o outro desenvolvedor.
- Não executar force push nem reescrever histórico compartilhado.

## Segurança
- Não versionar `.env`, credenciais, tokens, chaves de API, dumps ou dados reais de pacientes.
- Nunca enviar dados clínicos reais a serviços externos sem controles aprovados.
- Exigir autenticação, autorização por função e isolamento por clínica em todas as operações sensíveis.
- A IA não deve ter acesso direto ao banco nem executar SQL arbitrário.
- Operações clínicas exigem autorização e revisão de profissional habilitado; registrar auditoria das ações administrativas.

## Qualidade
- Fazer mudanças pequenas e verificáveis.
- Documentar comandos de instalação/teste e variáveis necessárias em `.env.example` sem segredos.
- Preferir testes automatizados para regras críticas de agendamento e permissões.
- Não presumir frameworks, estrutura ou regras de negócio ainda não definidos. Documentar decisões de arquitetura.
- Abrir Pull Request para `main` com resumo, testes e riscos.
