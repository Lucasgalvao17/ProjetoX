"""Mini-emulador do Firestore REST (list c/ paginação, get, create, patch, delete) para testes."""
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PROJETO = "projeto-teste"


class Armazem:
    def __init__(self):
        self.colecoes = {}
        self.lock = threading.Lock()
        self.contador = 0
        self.log = []

    def _agora(self):
        self.contador += 1
        t = datetime(2026, 11, 20, 12, 0, 0, self.contador, tzinfo=timezone.utc)
        s = t.strftime("%Y-%m-%dT%H:%M:%S.%f").rstrip("0").rstrip(".")  # fração de tamanho variável, como o Firestore
        return s + "Z"


ARMAZEM = Armazem()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _enviar(self, codigo, corpo=None):
        dados = json.dumps(corpo if corpo is not None else {}).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def _partes(self):
        u = urlparse(self.path)
        prefixo = f"/v1/projects/{PROJETO}/databases/(default)/documents/"
        assert u.path.startswith(prefixo), u.path
        resto = u.path[len(prefixo):].split("/")
        return resto[0], (resto[1] if len(resto) > 1 else None), parse_qs(u.query, keep_blank_values=True)

    def _doc(self, col, doc_id, d):
        return {"name": f"projects/{PROJETO}/databases/(default)/documents/{col}/{doc_id}",
                "fields": d["fields"], "createTime": d["create"], "updateTime": d["update"]}

    def _corpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        col, doc_id, q = self._partes()
        with ARMAZEM.lock:
            c = ARMAZEM.colecoes.setdefault(col, {})
            if doc_id is None:
                ids = list(c)
                tam = int(q.get("pageSize", ["20"])[0])
                ini = int(q.get("pageToken", ["0"])[0])
                fatia = ids[ini:ini + tam]
                out = {"documents": [self._doc(col, i, c[i]) for i in fatia]}
                if ini + tam < len(ids):
                    out["nextPageToken"] = str(ini + tam)
                return self._enviar(200, out)
            if doc_id not in c:
                return self._enviar(404, {"error": {"status": "NOT_FOUND", "message": "no document"}})
            return self._enviar(200, self._doc(col, doc_id, c[doc_id]))

    def do_POST(self):
        col, _, q = self._partes()
        corpo = self._corpo()
        with ARMAZEM.lock:
            c = ARMAZEM.colecoes.setdefault(col, {})
            doc_id = q.get("documentId", [None])[0]
            if doc_id is None:
                ARMAZEM.contador += 1
                doc_id = f"auto{ARMAZEM.contador:06d}"
            if doc_id in c:
                return self._enviar(409, {"error": {"status": "ALREADY_EXISTS", "message": "exists"}})
            agora = ARMAZEM._agora()
            c[doc_id] = {"fields": corpo.get("fields", {}), "create": agora, "update": agora}
            ARMAZEM.log.append(("POST", col, doc_id))
            return self._enviar(200, self._doc(col, doc_id, c[doc_id]))

    def do_PATCH(self):
        col, doc_id, q = self._partes()
        corpo = self._corpo()
        with ARMAZEM.lock:
            c = ARMAZEM.colecoes.setdefault(col, {})
            if doc_id not in c:
                return self._enviar(404, {"error": {"status": "NOT_FOUND", "message": "no document"}})
            for campo in q.get("updateMask.fieldPaths", []):
                c[doc_id]["fields"][campo] = corpo["fields"][campo]
            c[doc_id]["update"] = ARMAZEM._agora()
            ARMAZEM.log.append(("PATCH", col, doc_id))
            return self._enviar(200, self._doc(col, doc_id, c[doc_id]))

    def do_DELETE(self):
        col, doc_id, _ = self._partes()
        with ARMAZEM.lock:
            ARMAZEM.colecoes.setdefault(col, {}).pop(doc_id, None)
            ARMAZEM.log.append(("DELETE", col, doc_id))
        return self._enviar(200, {})


def iniciar():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"127.0.0.1:{srv.server_address[1]}"
