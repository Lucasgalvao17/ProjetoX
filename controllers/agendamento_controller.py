from utils.firebase_utils import inicializar_firebase
from datetime import datetime
import pandas as pd

db = inicializar_firebase()
COLLECTION_NAME = "reservas"

def listar():
    # Busca todas as reservas do Firebase Firestore e converte para DataFrame
    docs = db.collection(COLLECTION_NAME).stream()
    dados = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id  # Garante que o ID do documento é o identificador
        dados.append(d)
    
    if not dados:
        # Retorna um DataFrame vazio com as colunas esperadas se não houver registros
        return pd.DataFrame(columns=["id", "professor", "disciplina", "sala", "tipo_aula", "alunos", "data", "inicio", "fim", "status", "justificativa", "criado_por"])
    
    return pd.DataFrame(dados)

def conflitos(sala, data, inicio, fim, ignorar_id=None):
    df = listar()
    if df.empty:
        return df
    df = df[(df["sala"].astype(str) == str(sala)) &
            (df["data"].astype(str) == str(data)) &
            (df["status"].isin(["Pendente","Confirmada"]))]
    if ignorar_id is not None:
        df = df[df["id"].astype(str) != str(ignorar_id)]
    if df.empty:
        return df
    ini = datetime.strptime(str(inicio), "%H:%M").time()
    end = datetime.strptime(str(fim), "%H:%M").time()
    mask = []
    for _, r in df.iterrows():
        r_ini = datetime.strptime(str(r["inicio"]), "%H:%M").time()
        r_end = datetime.strptime(str(r["fim"]), "%H:%M").time()
        mask.append(ini < r_end and end > r_ini)
    return df[mask]

def horario_disponivel(sala, data, inicio, fim):
    return conflitos(sala, data, inicio, fim).empty

def criar(dados):
    # Grava diretamente no Firebase Firestore
    doc_ref = db.collection(COLLECTION_NAME).document()
    doc_ref.set(dados)
    return doc_ref.id

def alterar_status(id_reserva, status):
    # Atualiza o status diretamente no documento do Firebase
    doc_ref = db.collection(COLLECTION_NAME).document(str(id_reserva))
    doc_ref.update({"status": status})

def pd_to_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)
