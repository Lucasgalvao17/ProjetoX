# ATILA V2 — Gestão e Agendamento de Salas

## Tecnologias
Python + Streamlit + Pandas + CSV + MVC + Git + GitHub + VS Code.

## Novidades
- Login
- Criação de conta
- Perfis Administrador, Professor e Solicitante
- Logout
- Proteção das páginas
- Senhas armazenadas como hash SHA-256
- Cadastro de salas com recursos
- Recomendação de sala
- Validação de conflitos de horário
- Solicitação de reserva
- Aprovação/reprovação/cancelamento por administrador
- Filtros de agendamento
- Cadastro de disciplinas
- Gerenciamento de usuários
- Perfil
- Dashboard
- Persistência em CSV

## Login de teste
Administrador:
admin@atila.local
admin123

Professor:
ana@atila.local
ana123

## Executar
No Windows, execute `EXECUTAR_ATILA.bat`.

Ou:

```bash
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

## Git
```bash
git init
git add .
git commit -m "ATILA V2 - login e gestão de reservas"
git branch -M main
git remote add origin URL_DO_REPOSITORIO
git push -u origin main
```
