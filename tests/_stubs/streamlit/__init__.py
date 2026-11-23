"""Streamlit FALSO só para testes: executa as páginas reais sem servidor Streamlit."""
import sys


class StopExecution(Exception):
    pass


class SwitchPage(Exception):
    def __init__(self, destino):
        self.destino = destino


def cache_resource(*args, **kwargs):
    def decorar(f):
        memo = {}
        def envolvido(*a):
            if a not in memo:
                memo[a] = f(*a)
            return memo[a]
        return envolvido
    return decorar(args[0]) if args and callable(args[0]) else decorar


class _Ctx:
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def __getattr__(self, nome):
        return getattr(sys.modules[__name__], nome)


class _Sidebar(_Ctx):
    def __getattr__(self, nome):
        if nome == "page_link":
            return lambda pagina, *a, **k: SAIDA.append(("menu", pagina))
        if nome in ("markdown", "caption", "divider"):
            return lambda *a, **k: None
        if nome == "button":
            return lambda *a, **k: False
        raise AttributeError(nome)


secrets = {}
session_state = {}
query_params = {}   # st.query_params (o tema fica em ?tema=)
sidebar = _Sidebar()
SAIDA = []          # (tipo, texto) de tudo que a página "desenhou"
DADOS = {}          # DataFrames exibidos por st.dataframe, na ordem
ENTRADAS = {}       # rótulo -> valor que o "usuário" digitou/clicou


def resetar(entradas=None):
    SAIDA.clear(); DADOS.clear(); DADOS["lista"] = []
    ENTRADAS.clear(); ENTRADAS.update(entradas or {})


def _msg(tipo):
    def f(texto="", *a, **k):
        SAIDA.append((tipo, str(texto)))
    return f


for _t in ("error", "success", "warning", "info", "caption", "title", "header", "subheader", "write", "markdown"):
    globals()[_t] = _msg(_t)


def divider(*a, **k): pass
def set_page_config(*a, **k): pass


def stop(): raise StopExecution()
def rerun(): raise StopExecution()
def switch_page(destino): raise SwitchPage(destino)


def _entrada(rotulo, padrao, chave=None):
    for k in (chave, rotulo):
        if k is not None and k in ENTRADAS:
            return ENTRADAS[k]
    return padrao


def text_input(rotulo, value="", key=None, **k): return _entrada(rotulo, value, key)
def text_area(rotulo, value="", key=None, **k): return _entrada(rotulo, value, key)
def number_input(rotulo, min_value=None, max_value=None, value=None, *a, **k):
    if value is None and a: value = a[0]
    return _entrada(rotulo, value if value is not None else min_value, k.get("key"))
def date_input(rotulo, value=None, key=None, **k): return _entrada(rotulo, value, key)
def time_input(rotulo, value=None, key=None, **k): return _entrada(rotulo, value, key)
def selectbox(rotulo, opcoes, *a, **k):
    opcoes = list(opcoes)
    v = _entrada(rotulo, None, k.get("key"))
    if v is not None:
        return v
    return opcoes[k.get("index", 0) or 0] if opcoes else None
def multiselect(rotulo, opcoes=(), key=None, **k): return _entrada(rotulo, [], key)
def checkbox(rotulo, value=False, key=None, **k): return bool(_entrada(rotulo, value, key))
def button(rotulo, *a, **k): return bool(_entrada(rotulo, False, k.get("key")))
def form_submit_button(rotulo, *a, **k): return bool(_entrada(rotulo, False, k.get("key")))
def page_link(pagina, *a, **k): SAIDA.append(("link", pagina))
def form(*a, **k): return _Ctx()
def container(*a, **k): return _Ctx()
def tabs(rotulos):
    for r in rotulos: SAIDA.append(("tab", str(r)))
    return [_Ctx() for _ in rotulos]
def metric(rotulo, valor, *a, **k): SAIDA.append(("metric", f"{rotulo}={valor}"))


class _Coluna(_Ctx):
    def metric(self, rotulo, valor, *a, **k): SAIDA.append(("metric", f"{rotulo}={valor}"))
    def header(self, t, *a, **k): SAIDA.append(("header", t))
    def button(self, rotulo, *a, **k): return bool(_entrada(rotulo, False, k.get("key")))
    def text_input(self, rotulo, value="", key=None, **k): return _entrada(rotulo, value, key)


def columns(spec, *a, **k):
    n = spec if isinstance(spec, int) else len(spec)
    return [_Coluna() for _ in range(n)]


def dataframe(df, *a, **k): DADOS["lista"].append(df)
def markdown(texto="", *a, **k): SAIDA.append(("markdown", str(texto)))
