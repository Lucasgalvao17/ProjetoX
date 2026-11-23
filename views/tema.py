"""Identidade visual do ÁTILA, inspirada no portal da UNISAPIENS.

Para trocar uma cor do sistema inteiro, mude só o bloco :root logo abaixo (e, se for o caso, a
primaryColor em .streamlit/config.toml). Este arquivo não importa o Streamlit.
"""
from html import escape

# Texto sempre em roxo escuro sobre o laranja (contraste 6,5:1). O portal original usa branco
# sobre laranja (2,4:1), que cansa a leitura.
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700&family=Sora:wght@600;700;800&display=swap');

:root {
  --laranja: #F39200;
  --roxo-900: #2D1659;
  --roxo-600: #5B2D91;
  --verde-agua: #1F8A99;
  --superficie: #FFFFFF;
  --borda: #E1E3EE;
  --texto-suave: #5B5F73;
  --fonte-corpo: 'Nunito Sans', 'Segoe UI', system-ui, -apple-system, sans-serif;
  --fonte-titulo: 'Sora', 'Nunito Sans', 'Segoe UI', system-ui, sans-serif;
}

/* ---------- Tipografia (só em elementos de texto; ícones do Streamlit ficam intactos) ---------- */
.stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stMetricLabel"], .stApp [data-baseweb="tab"] {
  font-family: var(--fonte-corpo) !important;
}
.stApp [data-testid="stIconMaterial"] { font-family: "Material Symbols Rounded" !important; }
.stApp h1, .stApp h2, .stApp h3, .stApp [data-testid="stMetricValue"] {
  font-family: var(--fonte-titulo) !important;
  color: var(--roxo-900);
}

/* ---------- Página ---------- */
.block-container, [data-testid="stMainBlockContainer"] {
  max-width: 1320px;
  padding-top: 3rem;
}

/* Título da página: linha verde-água com marcador, como no portal da faculdade */
.stApp h1 {
  font-weight: 700;
  font-size: 1.9rem;
  line-height: 1.25;
  position: relative;
  padding-bottom: .75rem;
  margin-bottom: .35rem;
  border-bottom: 1px solid var(--verde-agua);
}
.stApp h1::after {
  content: "";
  position: absolute;
  left: 0;
  bottom: -3px;
  width: 64px;
  height: 5px;
  background: var(--verde-agua);
}
.stApp h2 { font-weight: 700; font-size: 1.4rem; }
.stApp h3 { font-weight: 600; font-size: 1.15rem; }
.stApp [data-testid="stCaptionContainer"] { color: var(--texto-suave); }

/* ---------- Menu lateral: laranja da faculdade, com texto roxo legível ---------- */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
  background: var(--laranja) !important;
}
[data-testid="stSidebarNav"] { display: none; }  /* menu automático: usamos o menu por perfil (views/layout.py) */
[data-testid="stSidebar"] * { color: var(--roxo-900) !important; }
[data-testid="stSidebar"] hr { border-color: rgba(45, 22, 89, .28) !important; }

[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
  border-radius: 10px;
  padding: .5rem .75rem;
  margin-bottom: 2px;
  transition: background-color .15s ease;
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] p { font-weight: 600; }
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
  background: rgba(45, 22, 89, .12);
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
  background: var(--roxo-900);
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"],
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] * {
  color: #FFFFFF !important;
}

/* Marca (topo do menu) */
.atila-marca { display: flex; align-items: center; gap: .75rem; padding: .25rem 0 .5rem; }
[data-testid="stSidebar"] .atila-marca__logo {
  width: 2.6rem; height: 2.6rem; flex: none;
  display: grid; place-items: center;
  border-radius: 12px;
  background: var(--roxo-900);
  color: var(--laranja) !important;
  font: 800 1.35rem/1 var(--fonte-titulo);
}
.atila-marca__nome { font: 800 1.3rem/1.1 var(--fonte-titulo); }
.atila-marca__sub { font-size: .8rem; font-weight: 600; line-height: 1.25; margin-top: 2px; }

/* Usuário logado */
.atila-usuario {
  display: flex; align-items: center; gap: .65rem;
  padding: .6rem .7rem;
  margin: .25rem 0 .75rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, .45);
}
[data-testid="stSidebar"] .atila-usuario__avatar {
  width: 2.3rem; height: 2.3rem; flex: none;
  display: grid; place-items: center;
  border-radius: 50%;
  background: var(--roxo-900);
  color: #FFFFFF !important;
  font: 700 .85rem/1 var(--fonte-titulo);
}
.atila-usuario__nome { font-weight: 700; font-size: .92rem; line-height: 1.2; overflow-wrap: anywhere; }
.atila-usuario__perfil { font-size: .8rem; font-weight: 600; }

/* Botão "Sair" do menu */
[data-testid="stSidebar"] .stButton button {
  background: transparent;
  border: 2px solid var(--roxo-900);
  border-radius: 10px;
  font-weight: 700;
}
[data-testid="stSidebar"] .stButton button:hover,
[data-testid="stSidebar"] .stButton button:hover * {
  background: var(--roxo-900);
  color: #FFFFFF !important;
}

/* ---------- Indicadores ---------- */
[data-testid="stMetric"] {
  background: var(--superficie);
  border: 1px solid var(--borda);
  border-left: 5px solid var(--laranja);
  border-radius: 10px;
  padding: .9rem 1.1rem;
}
[data-testid="stMetricLabel"] { color: var(--texto-suave); font-weight: 600; }
[data-testid="stMetricValue"] { font-weight: 700; }

/* ---------- Abas ---------- */
[data-baseweb="tab-list"] { gap: .25rem; }
button[data-baseweb="tab"] { font-weight: 600; padding: .6rem 1rem; }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--roxo-900); }
[data-baseweb="tab-highlight"] { background-color: var(--laranja) !important; height: 3px !important; }
[data-baseweb="tab-border"] { background-color: var(--borda) !important; }

/* ---------- Botões e campos ---------- */
.stApp .stButton button, .stApp [data-testid="stFormSubmitButton"] button {
  border-radius: 10px;
  font-weight: 700;
}
.stApp button[kind="primary"]:hover,
.stApp [data-testid="stBaseButton-primary"]:hover,
.stApp [data-testid="stBaseButton-primaryFormSubmit"]:hover {
  background-color: var(--roxo-900);
  border-color: var(--roxo-900);
}
.stApp [data-baseweb="input"], .stApp [data-baseweb="textarea"], .stApp [data-baseweb="select"] > div {
  border-radius: 10px;
}
.stApp [data-baseweb="input"]:focus-within, .stApp [data-baseweb="textarea"]:focus-within {
  border-color: var(--roxo-600) !important;
  box-shadow: 0 0 0 2px rgba(91, 45, 145, .25);
}
.stApp a:focus-visible, .stApp button:focus-visible {
  outline: 3px solid var(--roxo-600);
  outline-offset: 2px;
}

/* ---------- Tabelas, avisos e atalhos ---------- */
[data-testid="stDataFrame"] {
  border: 1px solid var(--borda);
  border-radius: 10px;
  overflow: hidden;
  background: var(--superficie);
}
[data-testid="stAlert"] { border-radius: 10px; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; background: var(--superficie); }

/* Atalhos da tela inicial do professor (links de página fora do menu) */
[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] {
  background: var(--superficie);
  border: 1px solid var(--borda);
  border-left: 5px solid var(--laranja);
  border-radius: 10px;
  padding: .9rem 1rem;
  transition: border-color .15s ease, box-shadow .15s ease;
}
[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] p { font-weight: 700; color: var(--roxo-900); }
[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:hover {
  border-color: var(--roxo-600);
  box-shadow: 0 2px 10px rgba(45, 22, 89, .12);
}

@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; }
}
"""

# Tela de entrada: sem menu lateral e com o painel laranja de boas-vindas.
CSS_LOGIN = """
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {
  display: none !important;
}
.block-container, [data-testid="stMainBlockContainer"] { max-width: 1080px; padding-top: 4rem; }

.atila-hero {
  min-height: 27rem;
  padding: 2.5rem 2.25rem;
  border-radius: 16px;
  background: var(--laranja);
  color: var(--roxo-900);
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}
.atila-hero__logo {
  width: 3.2rem; height: 3.2rem;
  display: grid; place-items: center;
  border-radius: 14px;
  background: var(--roxo-900);
  color: var(--laranja);
  font: 800 1.7rem/1 var(--fonte-titulo);
}
.atila-hero__titulo { font: 800 2.6rem/1.05 var(--fonte-titulo); }
.atila-hero__texto { font-size: 1.1rem; font-weight: 600; line-height: 1.45; max-width: 26rem; margin: 0; }
.atila-hero__lista { margin: auto 0 0; padding: 0; list-style: none; display: grid; gap: .6rem; }
.atila-hero__lista li {
  padding-left: 1.1rem;
  border-left: 4px solid var(--roxo-900);
  font-weight: 700;
  line-height: 1.3;
}

@media (max-width: 640px) {
  .atila-hero { min-height: auto; padding: 1.5rem 1.25rem; }
  .atila-hero__titulo { font-size: 2rem; }
}
"""


def iniciais(nome: str) -> str:
    partes = [p for p in str(nome or "").split() if p]
    if not partes:
        return "?"
    return (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()


def html_marca() -> str:
    return (
        '<div class="atila-marca"><div class="atila-marca__logo">Á</div>'
        '<div><div class="atila-marca__nome">ÁTILA</div>'
        '<div class="atila-marca__sub">Agendamento de salas<br>UNISAPIENS</div></div></div>'
    )


def html_usuario(nome: str, perfil: str) -> str:
    """Nome e perfil vêm do banco (digitados por usuários): sempre escapados."""
    return (
        '<div class="atila-usuario">'
        f'<div class="atila-usuario__avatar">{escape(iniciais(nome))}</div>'
        f'<div><div class="atila-usuario__nome">{escape(str(nome or ""))}</div>'
        f'<div class="atila-usuario__perfil">{escape(str(perfil or ""))}</div></div></div>'
    )


def html_hero_login() -> str:
    return (
        '<div class="atila-hero">'
        '<div class="atila-hero__logo">Á</div>'
        '<div class="atila-hero__titulo">ÁTILA</div>'
        '<p class="atila-hero__texto">Reserve salas e laboratórios da UNISAPIENS sem conflito de horário.</p>'
        '<ul class="atila-hero__lista">'
        '<li>Solicite uma sala em poucos cliques</li>'
        '<li>Acompanhe cada pedido: pendente, aprovado ou cancelado</li>'
        '<li>Veja quais salas estão livres antes de pedir</li>'
        '</ul></div>'
    )
