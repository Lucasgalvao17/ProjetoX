import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            # Converte os segredos do Streamlit diretamente para dicionário
            secrets_dict = dict(st.secrets["firebase"])
            
            cred = credentials.Certificate(secrets_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro crítico ao inicializar o Firebase: {e}")
            raise e
            
    return firestore.client()
