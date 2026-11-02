# Aplicativo desktop nativo

## Decisão

A partir desta implementação, o novo cliente local é Python 3.12 + PySide6/Qt Widgets, com SQLite pela biblioteca padrão. Não usa navegador, Electron, WebView, HTML ou servidor HTTP. O protótipo HTML anterior serviu de referência funcional; sua implementação não é o runtime do app.

O código fica em `desktop/`, na branch `frontend`. O banco embutido atende exclusivamente à demonstração offline deste cliente. Não estabelece nem altera contratos da futura API da branch `backend`. A integração futura deve ser coordenada antes de mudar schemas compartilhados.

## Executar no Windows

```powershell
cd desktop
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Após instalar as dependências, `desktop/iniciar.bat` abre a janela sem terminal persistente. No Linux/macOS, use `python3 -m venv .venv`, instale os requisitos e execute `.venv/bin/python main.py`.

## Executável Windows

A ação **Desktop checks and Windows build** testa e empacota em Windows. Quando a execução terminar com sucesso, baixe `Teha-Windows` em **Actions**, extraia a pasta inteira e abra `Teha.exe`. A pasta `_internal` deve permanecer junto do executável. Não é um instalador nem um binário com assinatura de código.

Para gerar localmente:

```powershell
.venv\Scripts\python.exe -m pip install pyinstaller==6.11.1
.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --onedir --name Teha main.py
```

## Funcionalidades desta base

- Menu recolhível, fundo branco, azul escuro, faixa multicolorida e perfil local com foto opcional.
- Pacientes em lista com busca e cadastro em diálogo separado; seis exemplos fictícios inseridos uma única vez.
- Agenda em calendário nativo com marca vermelha nos dias de consulta e caderneta do dia.
- Conflitos por paciente, profissional e sala, com validação transacional no SQLite.
- Sala de espera dentro da Agenda; somente consultas de hoje com chegada confirmada.
- Menu `⋯` por registro para editar, avaliar, iniciar/concluir atendimento e abrir prontuário.
- Avaliação inicial vinculada à consulta e ao paciente, com versões anteriores no prontuário.
- Anamnese, evolução e adendos preservados; odontograma em registros por dente FDI/face.
- Cadastros de equipe, tratamentos, documentos com revisão/impressão, receitas e despesas.
- Resumo financeiro e trilha de alterações local.
- Backup consistente do SQLite pela API de backup, inclusive com WAL ativo.

## Dados e recuperação

O banco fica na pasta local de dados do usuário fornecida pelo Qt (`QStandardPaths.AppLocalDataLocation`), sob `Sophion/TehaDemo`, e nunca na pasta do código. O caminho exato aparece em **Dados e backup**. O banco se chama `teha-demo.sqlite3`.

O backup é um arquivo SQLite **sem criptografia**. Para recuperar uma cópia: feche todas as instâncias do aplicativo, guarde uma cópia da pasta de dados atual e substitua `teha-demo.sqlite3` pelo backup. Não copie arquivos enquanto houver outra instância aberta. Arquivos auxiliares `-wal`/`-shm` de uma base anterior não devem acompanhar a base restaurada.

Os dados armazenados pelo HTML no navegador não são migrados automaticamente. Não há importação dos backups JSON/criptografados antigos nesta etapa.

## Limites explícitos

Esta é uma **base de demonstração com dados fictícios**, não uma versão pronta para operar uma clínica. Ainda faltam autenticação por chave, autorização real, isolamento por clínica, criptografia do banco/backup, sincronização local/nuvem, anexos, assinatura digital, migração dos dados do navegador e instalador assinado. A foto e o nome são apenas identificação visual. A auditoria local não é inviolável.

O odontograma nativo desta etapa é tabular, por dente e face; não reproduz ainda o desenho dentário do protótipo. Tratamentos e financeiro possuem lançamentos básicos, sem geração automática de parcelas ou cobrança integrada. A IA é apenas uma tela reservada, sem integração ou execução de ações.

## Testes

```powershell
cd desktop
python -m unittest discover -s tests -v
```

Em servidor sem tela, defina `QT_QPA_PLATFORM=offscreen`. Os testes verificam conflitos e adjacência de horários, chegada somente no dia da consulta, vínculo da triagem, preservação das revisões e evoluções, backup, exemplos sem duplicação e abertura das telas nativas com cadastro de paciente.

Referências: [Qt for Python](https://doc.qt.io/qtforpython-6/), [QCalendarWidget](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCalendarWidget.html).
