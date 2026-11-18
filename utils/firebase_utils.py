import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            fb_secrets = st.secrets["firebase"]
            cred_dict = dict(fb_secrets)
            
            # Pega a chave privada e limpa qualquer sujeira ou caractere inválido no início
            pk = str(cred_dict.get("private_key", ""))
            pk = pk.strip()
            
            # Remove eventuais barras invertidas duplicadas ou quebras iniciais indesejadas
            if pk.startswith("\\n"):
                pk = pk[2:]
            elif pk.startswith("\n"):
                pk = pk[1:]
                
            # Converte os caracteres literais '\n' em quebras de linha reais do sistema
            pk = pk.replace("\\n", "\n")
            
            cred_dict["private_key"] = pk
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro crítico ao inicializar o Firebase: {e}")
            raise e
            
    return firestore.client()
