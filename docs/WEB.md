# Teha web

Site: https://teha-odontologia.pages.dev/

Cliente em web/, publicado por Cloudflare Pages a partir da main. Build: npm ci && npm run build; saída dist. As variáveis SUPABASE_URL e SUPABASE_PUBLISHABLE_KEY são configuradas na Cloudflare, sem chaves secretas no cliente.

## Banco ativo

O projeto Supabase Clinica (zumftdfcfoxovpvtjknm), região São Paulo, recebeu o esquema web/database/schema.sql pela migração teha_records_auth_audit. O site aponta para esse projeto, substituindo o anterior.

teha_records guarda pacientes, consultas, triagens, prontuários, dentes, tratamentos, documentos, financeiro, equipe e configurações. teha_history guarda a auditoria. RLS restringe dados à conta autenticada; não há acesso anônimo. Este modelo ainda representa espaços individuais: compartilhar uma clínica entre contas e regras por função de equipe é uma próxima etapa.

Funções: teha_save (validação e controle de versão), teha_import (inserção em lote transacional sem substituir registros existentes) e teha_seed_demo (seis pacientes fictícios e profissional de exemplo, uma vez por conta). Prontuários e registros dentários são preservados; correções exigem novo registro.

Verificação no banco: gravação, lote de dentes, bloqueio de sobrescrita de prontuário e isolamento entre contas passaram em transação descartada, sem deixar usuários ou registros de teste. Advisors de segurança sem alertas após a migração. Ainda não foi feita uma avaliação completa para uso clínico real.

## Acesso

Entre em Entrar na nuvem com e-mail/senha ou crie uma conta. Se o projeto exigir confirmação de e-mail, confirme antes de entrar. A sessão fica no sessionStorage da aba. Na mesma conta, os dados persistem entre dispositivos. Sem login, a demonstração continua temporária e reinicia ao recarregar; ela não envia dados ao banco.

A IA continua desativada. Assinatura digital, acesso compartilhado por equipe e avaliação integral de recuperação/uso clínico permanecem pendentes.

## Desenvolvimento

cd web; npm ci; configure SUPABASE_URL e SUPABASE_PUBLISHABLE_KEY no ambiente; npm run build; npm test. Sirva dist por HTTP.
