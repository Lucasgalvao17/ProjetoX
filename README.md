# ATILA — Gestão e Agendamento de Salas

Python + Streamlit + **Cloud Firestore** (projeto `reserva-salas-bb922`).
Todos os dados (salas, reservas, usuários, disciplinas) vivem no Firestore e **todas as telas,
inclusive o Dashboard, leem pela mesma camada** (`utils/firestore_client.py` → `controllers/*`).
Não há CSV de dados nem cache: o que uma aba grava aparece nas outras na hora.

## Estrutura
```
app.py                         Dashboard (entrada)
pages/                         Login, Salas, Nova Reserva, Agendamentos, Usuários, Disciplinas, Perfil
controllers/                   sala_, agendamento_, usuario_, disciplina_, dashboard_controller
utils/firestore_client.py      ÚNICO cliente REST do Firestore (paginação, erros, tipos)
utils/auth.py                  login/sessão (usuários no Firestore, senha PBKDF2 com sal)
data/seed/                     CSVs usados UMA vez para popular coleções vazias (usuarios, disciplinas)
firestore.rules                regras (bloqueia acesso direto de navegadores)
tests/                         58 testes (Firestore falso + páginas)
```

Coleções: `salas`, `reservas`, `usuarios`, `disciplinas`.

## Configuração (Firebase + Streamlit Cloud)
1. Firebase Console → Configurações do projeto → Contas de serviço → **Gerar nova chave privada**.
2. Streamlit Cloud → app → Settings → **Secrets**: cole conforme `.streamlit/secrets.toml.example`.
3. Faça deploy e confirme que o Dashboard abre sem o aviso de "modo legado".
4. Firebase Console → Firestore → Regras: publique o conteúdo de `firestore.rules`.
5. Google Cloud Console → IAM → Contas de serviço: **exclua a chave antiga** (a que estava em `utils/serviceAccountKey.json`).
6. Entre uma vez com o admin inicial e troque a senha em *Meu Perfil*; depois remova `data/seed/usuarios.csv`.

## Rodar localmente
```bash
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
# copie .streamlit/secrets.toml.example para .streamlit/secrets.toml e preencha
.venv\Scripts\python.exe -m streamlit run app.py
```

## Testes (não precisam de internet nem de credenciais)
```bash
python -m unittest discover -s tests -t . -v
```

## Regras de reserva
- Conflito = mesma sala + mesma data + intervalo sobreposto com reserva **Pendente** ou **Confirmada**.
- Validado ao criar, ao reativar uma reserva (Pendente/Confirmada) e re-conferido após gravar
  (se duas pessoas reservam ao mesmo tempo, a que chegou depois é desfeita).
- Só admin aprova/reprova/cancela e cadastra/exclui salas; sala com reserva ativa não pode ser excluída.
