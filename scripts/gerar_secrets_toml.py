"""
Gera o bloco de Secrets (TOML) a partir do .json da conta de serviço baixado do Firebase,
sem copiar/colar a chave à mão (que é onde caracteres se perdem).

Uso (no seu computador):
    python scripts/gerar_secrets_toml.py "C:\\caminho\\reserva-salas-bb922-firebase-adminsdk-xxxx.json"

O bloco é impresso NO TERMINAL: copie-o dali e cole em Streamlit Cloud > Settings > Secrets.
Com --salvar, grava em .streamlit/secrets.toml (já ignorado pelo Git) para rodar localmente.
Nunca cole a chave em chats, e-mails ou no repositório.
"""
import json
import re
import sys
from pathlib import Path

CAMPOS = ("type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "token_uri")


def main(argv):
    salvar = "--salvar" in argv
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)

    dados = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    faltando = [c for c in CAMPOS if not str(dados.get(c, "")).strip()]
    if faltando:
        sys.exit(f"ERRO: o JSON não tem os campos: {', '.join(faltando)}. É mesmo a chave de conta de serviço?")

    m = re.search(r"-----BEGIN PRIVATE KEY-----(.*?)-----END PRIVATE KEY-----", dados["private_key"], re.S)
    corpo = re.sub(r"[^A-Za-z0-9+/=]", "", m.group(1)) if m else ""
    if not m or len(corpo) % 4 != 0:
        sys.exit("ERRO: a private_key deste arquivo está corrompida. Baixe uma chave nova no Firebase.")

    try:  # validação extra, se a biblioteca estiver instalada
        from cryptography.hazmat.primitives import serialization
        serialization.load_pem_private_key(dados["private_key"].encode(), password=None)
    except ImportError:
        pass
    except Exception as exc:
        sys.exit(f"ERRO: a chave não é uma chave RSA válida ({type(exc).__name__}).")

    linhas = ["[firestore]", f"project_id = {json.dumps(dados['project_id'])}", "", "[gcp_service_account]"]
    linhas += [f"{c} = {json.dumps(dados[c])}" for c in CAMPOS]   # json.dumps => string TOML válida, \n escapado
    bloco = "\n".join(linhas) + "\n"

    if salvar:
        destino = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
        destino.parent.mkdir(exist_ok=True)
        destino.write_text(bloco, encoding="utf-8")
        print(f"OK: gravado em {destino} (ignorado pelo Git).")
    else:
        print("# ---- COPIE DAQUI PARA BAIXO e cole em Settings > Secrets ----")
        print(bloco)
        print("# ---- fim ----", file=sys.stderr)
        print(f"# Chave OK: corpo com {len(corpo)} caracteres, múltiplo de 4.", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
