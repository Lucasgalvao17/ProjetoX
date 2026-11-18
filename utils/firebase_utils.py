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
                st.error("Erro crítico: O arquivo serviceAccountKey.json não foi encontrado na pasta utils!")
                raise FileNotFoundError("Arquivo de credenciais do Firebase não encontrado.")
                
        except Exception as e:
            st.error(f"Erro crítico ao inicializar o Firebase: {e}")
            raise e
            
    return firestore.client()
