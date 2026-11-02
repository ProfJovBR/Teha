# Teha

Aplicativo desktop para gestão de consultórios odontológicos. Cliente local em **Python + PySide6 (Qt Widgets)** e **SQLite**, sem navegador ou servidor web.

**Estado atual: demonstração offline, somente com dados fictícios.** Autenticação, permissões reais e sincronização em nuvem continuam pendentes.

## Começar

```powershell
cd desktop
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Na primeira execução são criados seis pacientes fictícios e um profissional de demonstração. O banco fica na pasta de dados do usuário, fora do repositório.

[Instalação, executável Windows, funcionalidades e limites](docs/DESKTOP.md).

[Fluxo de colaboração](docs/WORKFLOW.md). Alterações da `frontend` e da `backend` chegam à `main` por Pull Request.
