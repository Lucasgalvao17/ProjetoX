import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import google.auth.transport.requests
from google.oauth2 import service_account

def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            fb_secrets = st.secrets["firebase"]
            
            # Reconstrói o dicionário garantindo que todos os campos sejam strings puras do Python
            cred_dict = {
                "type": str(fb_secrets["type"]),
                "project_id": str(fb_secrets["project_id"]),
                "private_key_id": str(fb_secrets["private_key_id"]),
                "private_key": str(fb_secrets["private_key"]).replace("\\n", "\n"),
                "client_email": str(fb_secrets["client_email"]),
                "client_id": str(fb_secrets["client_id"]),
                "auth_uri": str(fb_secrets["auth_uri"]),
                "token_uri": str(fb_secrets["token_uri"]),
                "auth_provider_x509_cert_url": str(fb_secrets["auth_provider_x509_cert_url"]),
                "client_x509_cert_url": str(fb_secrets["client_x509_cert_url"]),
                "universe_domain": str(fb_secrets.get("universe_domain", "googleapis.com"))
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro crítico ao inicializar o Firebase: {e}")
            raise e
            
    return firestore.client()
