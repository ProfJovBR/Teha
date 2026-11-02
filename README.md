# Teha

Sistema web para consultórios odontológicos, com o layout original aprovado: branco e azul escuro, menu recolhível, agenda, sala de espera e prontuário.

[Site na Cloudflare](https://teha-odontologia.pages.dev) · [Documentação da versão web](docs/WEB.md)

Código em `web/`. Cloudflare Pages publica a `main`. Supabase vinculado ao projeto; a configuração das novas tabelas está preparada, **pendente de autorização após bloqueio de revisão automática**.

O site abre em demonstração com seis pacientes fictícios e dados temporários. A autenticação está conectada ao Supabase; a gravação dos módulos na nuvem depende da aplicação do esquema documentado. Não usar dados reais nesta etapa.

A implementação desktop anterior está em `desktop/`, mantida como histórico. [Fluxo de colaboração](docs/WORKFLOW.md).
