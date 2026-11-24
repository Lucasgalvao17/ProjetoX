# ATILA — Gestão e Agendamento de Salas

Python + Streamlit + **Cloud Firestore** (projeto `reserva-salas-bb922`).
Todos os dados (salas, reservas, usuários, disciplinas) vivem no Firestore e **todas as telas,
inclusive o Dashboard, leem pela mesma camada** (`utils/firestore_client.py` → `controllers/*`).
Não há CSV de dados nem cache: o que uma aba grava aparece nas outras na hora.

## Estrutura
```
app.py                         Dashboard (entrada)
pages/                         Login, Salas, Nova Reserva, Agendamentos, Usuários, Disciplinas, Perfil,
                               Minhas Reservas e Disponibilidade (professor)
controllers/                   sala_, agendamento_, usuario_, disciplina_, dashboard_controller
utils/firestore_client.py      ÚNICO cliente REST do Firestore (paginação, erros, tipos)
utils/auth.py                  login/sessão (usuários no Firestore, senha PBKDF2 com sal)
utils/tempo.py                 hora local do sistema (padrão America/Porto_Velho; mude com ATILA_FUSO)
views/layout.py                menu por perfil + avisos; views/reservas_view.py = as 4 tabelas
data/seed/                     CSVs usados UMA vez para popular coleções vazias (usuarios, disciplinas)
firestore.rules                regras (bloqueia acesso direto de navegadores)
tests/                         127 testes (Firestore falso + páginas)
```

Coleções: `salas`, `reservas`, `usuarios`, `disciplinas` (e `config`, só com o marcador de que a carga inicial de disciplinas já foi feita).

## Perfis
| | Professor / Solicitante | Administrador |
|---|---|---|
| Início | resumo das próprias reservas | Dashboard completo |
| Reservas | solicitar, acompanhar as suas, cancelar as suas | aprovar, reprovar, cancelar, reabrir (todas) |
| Salas | só consulta disponibilidade | cadastrar, **editar**, excluir |
| Disciplinas | escolhe na lista | cadastrar, editar, ativar/desativar, **excluir** |
| Usuários | altera a própria senha | criar, editar perfil, ativar/desativar, redefinir senha |

## Tela de Agendamentos (4 tabelas)
**Aprovados** (confirmadas por vir) · **Pendentes** · **Cancelados** · **Histórico** (reprovadas + aprovadas já realizadas).
Reprovar/cancelar só muda o `status` (e grava `motivo`, `atualizado_por`, `atualizado_em`): o documento nunca é apagado.
"Concluída" é calculado pela data/hora, sem gravar nada.

## Configuração (Firebase + Streamlit Cloud)
1. Firebase Console → Configurações do projeto → Contas de serviço → **Gerar nova chave privada**.
2. Gere o bloco de Secrets SEM copiar à mão: `python scripts/gerar_secrets_toml.py "caminho\chave.json"` e cole a saída em Streamlit Cloud → app → Settings → **Secrets** (modelo em `.streamlit/secrets.toml.example`).
3. Faça deploy e confirme que o Dashboard abre sem o aviso de "modo legado".
4. Firebase Console → Firestore → Regras: publique o conteúdo de `firestore.rules`.
5. Google Cloud Console → IAM → Contas de serviço: **exclua a chave antiga** (a que estava em `utils/serviceAccountKey.json`; o arquivo já foi removido do projeto, mas a chave continua válida até ser revogada lá).
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

## Dashboard (admin) — Agendamentos recentes
Mostra as 10 reservas mais recentes **de hoje em diante** (sem as reprovadas). Quando o dia da aula passa, ela sai da lista
sozinha: é só filtro de exibição, nada é apagado — o registro continua em Agendamentos → Histórico.
Se houver solicitações pendentes por vir, aparece um aviso com atalho para a análise.

## Excluir disciplina
Página Disciplinas → aba **Excluir disciplina** (pede confirmação). É bloqueada se houver reserva Pendente/Confirmada
ainda por vir com aquela disciplina; reservas realizadas/canceladas/reprovadas guardam o nome e o histórico não muda.
Para só esconder da Nova Reserva, use *Editar / ativar* e desative.

## Regras de reserva
- Conflito = mesma sala + mesma data + intervalo sobreposto com reserva **Pendente** ou **Confirmada**.
- Validado ao criar, ao reativar uma reserva (Pendente/Confirmada) e re-conferido após gravar
  (se duas pessoas reservam ao mesmo tempo, a que chegou depois é desfeita).
- Só admin aprova/reprova/cancela e cadastra/exclui salas; sala com reserva ativa não pode ser excluída.
