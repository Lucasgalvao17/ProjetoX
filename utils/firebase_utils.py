import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os

def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            caminho_json = os.path.join("utils", "serviceAccountKey.json")
            
            if os.path.exists(caminho_json):
                cred = credentials.Certificate(caminho_json)
                firebase_admin.initialize_app(cred)
            else:
                st.error(f"Erro crítico: O arquivo não foi encontrado em {caminho_json}!")
                raise FileNotFoundError("Arquivo de credenciais do Firebase não encontrado.")
                
        except Exception as e:
            st.error(f"Erro crítico ao inicializar o Firebase: {e}")
            raise e
            
    return firestore.client()
