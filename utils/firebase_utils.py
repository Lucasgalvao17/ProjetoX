import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            # Pega os segredos do Streamlit
            fb_secrets = st.secrets["firebase"]
            
            # Monta o dicionário de credenciais explicitamente
            cred_dict = {
                "type": fb_secrets["type"],
                "project_id": fb_secrets["project_id"],
                "private_key_id": fb_secrets["private_key_id"],
                "private_key": fb_secrets["private_key"].strip(),
                "client_email": fb_secrets["client_email"],
                "client_id": fb_secrets["client_id"],
                "auth_uri": fb_secrets["auth_uri"],
                "token_uri": fb_secrets["token_uri"],
                "auth_provider_x509_cert_url": fb_secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": fb_secrets["client_x509_cert_url"],
                "universe_domain": fb_secrets.get("universe_domain", "googleapis.com")
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro crítico ao inicializar o Firebase: {e}")
            raise e
            
    return firestore.client()
