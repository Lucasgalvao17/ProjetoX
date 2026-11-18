import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            fb_secrets = st.secrets["firebase"]
            cred_dict = dict(fb_secrets)
            
            # Limpa e normaliza a chave privada substituindo qualquer variação de quebra escapada
            pk = str(cred_dict.get("private_key", ""))
            
            # Se vier com barras escapadas duplas ou simples, normaliza para \n reais
            pk = pk.replace("\\\\n", "\n").replace("\\n", "\n")
            
            cred_dict["private_key"] = pk
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro crítico ao inicializar o Firebase: {e}")
            raise e
            
    return firestore.client()
