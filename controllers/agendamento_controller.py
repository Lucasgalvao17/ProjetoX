from utils.firebase_utils import inicializar_firebase
from datetime import datetime
import pandas as pd

db = inicializar_firebase()
COLLECTION_NAME = "reservas"

def listar():
    try:
        docs = list(db.collection(COLLECTION_NAME).stream())
        dados = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            dados.append(d)
        
        if not dados:
            return pd.DataFrame(columns=["id", "professor", "disciplina", "sala", "tipo_aula", "alunos", "data", "inicio", "fim", "status", "justificativa", "criado_por"])
        
        return pd.DataFrame(dados)
    except Exception:
        return pd.DataFrame(columns=["id", "professor", "disciplina", "sala", "tipo_aula", "alunos", "data", "inicio", "fim", "status", "justificativa", "criado_por"])

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
        r_end = datetime.strptime(str(r["end"] if "end" in r else r["fim"]), "%H:%M").time() if "end" in r or "fim" in r else datetime.strptime("16:00", "%H:%M").time()
        # Tratamento seguro para horários
        try:
            r_end = datetime.strptime(str(r["fim"]), "%H:%M").time()
        except:
            pass
        mask.append(ini < r_end and end > r_ini)
    return df[mask]

def horario_disponivel(sala, data, inicio, fim):
    return conflitos(sala, data, inicio, fim).empty

def criar(dados):
    doc_ref = db.collection(COLLECTION_NAME).document()
    doc_ref.set(dados)
    return doc_ref.id

def alterar_status(id_reserva, status):
    doc_ref = db.collection(COLLECTION_NAME).document(str(id_reserva))
    doc_ref.update({"status": status})

def pd_to_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)
