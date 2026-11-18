import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

def inicializar_firebase():
    # Verifica se já existe uma app do Firebase inicializada para evitar conflitos
    if not firebase_admin._apps:
        try:
            # Tenta carregar dos segredos do Streamlit Cloud
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                # Garante que as quebras de linha da chave privada sejam respeitadas
                if "private_key" in cred_dict:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            else:
                # Fallback para ficheiro local caso esteja a testar noutro ambiente
                cred = credentials.Certificate("utils/serviceAccountKey.json")
                firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro crítico ao inicializar o Firebase: {e}")
            raise e
            
    return firestore.client()
