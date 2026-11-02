# Teha web — retorno ao layout aprovado

A versão web preserva o HTML/CSS e os fluxos do protótipo `consultorio.html`: menu recolhível, fundo branco, azul escuro, borda colorida, agenda com calendário e sala de espera. O desktop foi descontinuado como direção do produto, sem apagar seu histórico.

## Publicação

- Repositório: `ProfJovBR/Teha`, diretório `web/`.
- Cloudflare Pages: projeto `teha-odontologia`, branch de produção `main`.
- Build: `npm ci && npm run build`; raiz `web`; saída `dist`.
- Supabase existente: `SiteDraMarianaDashBoard` (`zfkkdpwedxcnqstyksdy`), reativado.
- Build recebe `SUPABASE_URL` e `SUPABASE_PUBLISHABLE_KEY`. Nunca usar chave secreta/service_role no frontend.

## Situação do banco — bloqueio explícito

A autenticação está conectada ao Supabase. As novas tabelas `teha_records` e `teha_history`, funções, validações e políticas estão **preparadas em `web/database/schema.sql`, mas não foram aplicadas**: a revisão automática bloqueou DDL por interpretar o AGENTS.md como proibição de acesso da IA ao banco. Não contornar esse bloqueio. A aplicação depende de autorização explícita do proprietário para aplicar esse arquivo.

As tabelas legadas existentes foram somente inspecionadas, sem alteração. Há um problema legado: `public.appointment_reminders` está sem RLS. O site não utiliza essa tabela. A correção exige definir políticas conforme os vínculos da clínica antes de habilitar RLS.

Sem as novas tabelas, a página abre em **demonstração temporária**, com seis pacientes fictícios e um profissional fictício. Recarregar reinicia os exemplos; nenhum registro da demonstração é enviado ao banco. A tela e os avisos identificam esse modo. A conexão de dados autenticada só funciona depois da configuração do esquema; antes disso, o erro é explícito e há retorno à demonstração.

## Contrato proposto para revisão

`teha_records(owner_id,store,id,data,version,updated_at)` mantém os registros por conta autenticada. RLS restringe leitura/escrita ao `auth.uid()` proprietário. Nenhum acesso anônimo, exclusão de prontuários ou compartilhamento entre contas é permitido. Esse modelo representa um espaço individual de avaliação, **não uma clínica com equipe compartilhada**. Regras por clínica/equipe precisarão ser coordenadas com o backend antes de ampliar o acesso.

`teha_save` implementa controle de versão, validação de vínculos e conflitos de agenda; `teha_history` é escrito por trigger interna e somente lido pelo cliente. `teha_import` adiciona registros em transação, recusando IDs existentes; não apaga dados atuais. `teha_seed_demo` cria exemplos por conta uma única vez. A IA continua desativada, sem acesso a banco, SQL ou ferramentas.

## Executar e testar

```sh
cd web
npm ci
export SUPABASE_URL=https://SEU-PROJETO.supabase.co
export SUPABASE_PUBLISHABLE_KEY=SUA-CHAVE-PUBLICAVEL
npm run build
npm test
```

Sirva `web/dist` por HTTP. Login usa e-mail/senha via Supabase Auth, com confirmação por e-mail conforme configuração do projeto. A sessão fica no sessionStorage da aba. Não há credenciais fixas de administrador no código.

Para testar o layout, clique em **Visualizar demonstração** ou abra o site sem sessão. Não inserir dados reais de pacientes nesta versão. Banco e políticas pendentes; nenhum teste de gravação em nuvem foi apresentado como aprovado.
