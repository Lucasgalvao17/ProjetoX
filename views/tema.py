"""Identidade visual do ÁTILA, inspirada no portal da UNISAPIENS.

Para trocar uma cor do sistema inteiro, mude só o bloco :root logo abaixo (tema claro) e o bloco
:root de CSS_ESCURO (tema escuro) e, se for o caso, a primaryColor em .streamlit/config.toml.
Este arquivo não importa o Streamlit: quem escolhe o tema é views/layout.py (botão "Modo escuro").
"""
from html import escape

MODOS = ("claro", "escuro")

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

  /* Papéis de cor: o tema escuro (CSS_ESCURO) troca só estes valores. */
  --fundo: #F3F4F9;              /* espelha backgroundColor do config.toml */
  --campo: #FFFFFF;
  --texto: #1E1B2E;              /* espelha textColor do config.toml */
  --titulo: var(--roxo-900);
  --foco: var(--roxo-600);
  --foco-sombra: rgba(91, 45, 145, .25);
  --sombra: rgba(45, 22, 89, .12);
  --btn-hover: var(--roxo-900);
  --menu-fundo: var(--laranja);
  --menu-texto: var(--roxo-900);
  --menu-divisor: rgba(45, 22, 89, .28);
  --menu-hover: rgba(45, 22, 89, .12);
  --menu-cartao: rgba(255, 255, 255, .45);
  --menu-ativo-fundo: var(--roxo-900);
  --menu-ativo-texto: #FFFFFF;
  --marca-fundo: var(--roxo-900);
  --marca-texto: var(--laranja);
  --avatar-fundo: var(--roxo-900);
  --avatar-texto: #FFFFFF;
  --hero-fundo: var(--laranja);
  --hero-texto: var(--roxo-900);
  --hero-logo-fundo: var(--roxo-900);
  --hero-logo-texto: var(--laranja);
  --hero-traco: var(--roxo-900);
  --borda-forte: #AEB3CC;        /* borda bem visível de cartões (ex.: formulário de login) */

  /* Avisos (st.info / success / warning / error): fundo, borda e texto definidos aqui, com contraste
     mínimo de 7:1 (texto x fundo), para não depender do tema claro nativo do Streamlit. */
  --info-fundo: #E3F4F7;    --info-borda: #1F8A99;    --info-texto: #0B3C45;
  --ok-fundo: #E4F5EA;      --ok-borda: #2E9E5B;      --ok-texto: #0F3D22;
  --aviso-fundo: #FFF3DC;   --aviso-borda: #D98A00;   --aviso-texto: #4A3000;
  --erro-fundo: #FDE8EC;    --erro-borda: #D93A57;    --erro-texto: #5C0F1F;

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
  color: var(--titulo);
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
  background: var(--menu-fundo) !important;
}
[data-testid="stSidebarNav"] { display: none; }  /* menu automático: usamos o menu por perfil (views/layout.py) */
[data-testid="stSidebar"] * { color: var(--menu-texto) !important; }
[data-testid="stSidebar"] hr { border-color: var(--menu-divisor) !important; }

[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
  border-radius: 10px;
  padding: .5rem .75rem;
  margin-bottom: 2px;
  transition: background-color .15s ease;
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] p { font-weight: 600; }
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
  background: var(--menu-hover);
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
  background: var(--menu-ativo-fundo);
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"],
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] * {
  color: var(--menu-ativo-texto) !important;
}

/* Marca (topo do menu) */
.atila-marca { display: flex; align-items: center; gap: .75rem; padding: .25rem 0 .5rem; }
[data-testid="stSidebar"] .atila-marca__logo {
  width: 2.6rem; height: 2.6rem; flex: none;
  display: grid; place-items: center;
  border-radius: 12px;
  background: var(--marca-fundo);
  color: var(--marca-texto) !important;
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
  background: var(--menu-cartao);
}
[data-testid="stSidebar"] .atila-usuario__avatar {
  width: 2.3rem; height: 2.3rem; flex: none;
  display: grid; place-items: center;
  border-radius: 50%;
  background: var(--avatar-fundo);
  color: var(--avatar-texto) !important;
  font: 700 .85rem/1 var(--fonte-titulo);
}
.atila-usuario__nome { font-weight: 700; font-size: .92rem; line-height: 1.2; overflow-wrap: anywhere; }
.atila-usuario__perfil { font-size: .8rem; font-weight: 600; }

/* Botão "Sair" do menu */
[data-testid="stSidebar"] .stButton button {
  background: transparent;
  border: 2px solid var(--menu-texto);
  border-radius: 10px;
  font-weight: 700;
}
[data-testid="stSidebar"] .stButton button:hover,
[data-testid="stSidebar"] .stButton button:hover * {
  background: var(--menu-ativo-fundo);
  color: var(--menu-ativo-texto) !important;
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
button[data-baseweb="tab"][aria-selected="true"] { color: var(--titulo); }
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
  background-color: var(--btn-hover);
  border-color: var(--btn-hover);
}
.stApp [data-baseweb="input"], .stApp [data-baseweb="textarea"], .stApp [data-baseweb="select"] > div {
  border-radius: 10px;
}
.stApp [data-baseweb="input"]:focus-within, .stApp [data-baseweb="textarea"]:focus-within {
  border-color: var(--foco) !important;
  box-shadow: 0 0 0 2px var(--foco-sombra);
}
.stApp a:focus-visible, .stApp button:focus-visible {
  outline: 3px solid var(--foco);
  outline-offset: 2px;
}

/* ---------- Tabelas, avisos e atalhos ---------- */
[data-testid="stDataFrame"] {
  border: 1px solid var(--borda);
  border-radius: 10px;
  overflow: hidden;
  background: var(--superficie);
}

/* Avisos: o Streamlit pinta o fundo claro em um elemento INTERNO do aviso (varia com a versão). Por isso o
   fundo/borda ficam no [data-testid="stAlert"] e todo descendente fica transparente, com texto na cor do par. */
.stApp [data-testid="stAlert"] {
  --a-fundo: var(--info-fundo); --a-borda: var(--info-borda); --a-texto: var(--info-texto);
  background: var(--a-fundo) !important;
  background-color: var(--a-fundo) !important;
  border: 1px solid var(--a-borda) !important;
  border-left: 5px solid var(--a-borda) !important;
  border-radius: 10px !important;
  overflow: hidden;
}
.stApp [data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]),
.stApp [data-testid="stAlert"]:has([data-baseweb="notification"][kind="positive"]) {
  --a-fundo: var(--ok-fundo); --a-borda: var(--ok-borda); --a-texto: var(--ok-texto);
}
.stApp [data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]),
.stApp [data-testid="stAlert"]:has([data-baseweb="notification"][kind="warning"]) {
  --a-fundo: var(--aviso-fundo); --a-borda: var(--aviso-borda); --a-texto: var(--aviso-texto);
}
.stApp [data-testid="stAlert"]:has([data-testid="stAlertContentError"]),
.stApp [data-testid="stAlert"]:has([data-baseweb="notification"][kind="negative"]) {
  --a-fundo: var(--erro-fundo); --a-borda: var(--erro-borda); --a-texto: var(--erro-texto);
}
.stApp [data-testid="stAlert"] * {
  background: transparent !important;
  background-color: transparent !important;
  border-color: transparent !important;
  color: var(--a-texto) !important;
  -webkit-text-fill-color: var(--a-texto) !important;
}
.stApp [data-testid="stAlert"] svg { fill: var(--a-texto) !important; color: var(--a-texto) !important; }
.stApp [data-testid="stAlert"] a { text-decoration: underline; }
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
[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] p { font-weight: 700; color: var(--titulo); }
[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:hover {
  border-color: var(--foco);
  box-shadow: 0 2px 10px var(--sombra);
}

@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; }
}
"""

# Tema escuro: vem DEPOIS do CSS claro (mesma especificidade, o último ganha). Troca os papéis de cor
# e repinta os componentes nativos do Streamlit, que continuam com o tema claro do config.toml.
CSS_ESCURO = """
:root {
  color-scheme: dark;            /* barras de rolagem e controles nativos escuros */
  --superficie: #1F1A2E;
  --fundo: #15111F;
  --campo: #292238;
  --borda: #3A3252;
  --borda-tabela: #C9CFE0;       /* a tabela é invertida por filtro (abaixo): esta cor sai escura */
  --texto: #ECE9F5;
  --texto-suave: #B6B0CC;
  --titulo: #FFFFFF;
  --verde-agua: #3BB5C6;
  --foco: #FFB347;
  --foco-sombra: rgba(255, 179, 71, .30);
  --sombra: rgba(0, 0, 0, .55);
  --btn-hover: #FFA826;
  --menu-fundo: var(--roxo-900);
  --menu-texto: #F4F1FF;
  --menu-divisor: rgba(255, 255, 255, .22);
  --menu-hover: rgba(255, 255, 255, .10);
  --menu-cartao: rgba(255, 255, 255, .08);
  --menu-ativo-fundo: var(--laranja);
  --menu-ativo-texto: var(--roxo-900);
  --marca-fundo: var(--laranja);
  --marca-texto: var(--roxo-900);
  --avatar-fundo: var(--laranja);
  --avatar-texto: var(--roxo-900);
  --hero-fundo: var(--roxo-900);
  --hero-texto: #F4F1FF;
  --hero-logo-fundo: var(--laranja);
  --hero-logo-texto: var(--roxo-900);
  --hero-traco: var(--laranja);
  --borda-forte: #7C6FA8;

  /* Avisos no escuro: fundo escuro tingido, borda viva e texto claro (contraste > 10:1). */
  --info-fundo: #0F2F38;    --info-borda: #3BB5C6;    --info-texto: #E3F7FA;
  --ok-fundo: #0F2E1D;      --ok-borda: #3FB67A;      --ok-texto: #E2F8EC;
  --aviso-fundo: #38290B;   --aviso-borda: #FFB347;   --aviso-texto: #FFF1D6;
  --erro-fundo: #3B1420;    --erro-borda: #F0627A;    --erro-texto: #FFE3E8;
}

/* ---------- Página e cabeçalho ---------- */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {
  background-color: var(--fundo) !important;
}
[data-testid="stHeader"] * { color: var(--texto) !important; }

/* ---------- Texto ---------- */
.stApp p, .stApp li, .stApp label, .stApp small, .stApp summary, .stApp th, .stApp td,
.stApp h4, .stApp h5, .stApp h6 { color: var(--texto); }
.stApp h1, .stApp h2, .stApp h3, .stApp h1 *, .stApp h2 *, .stApp h3 *,
.stApp [data-testid="stMetricValue"], .stApp [data-testid="stMetricValue"] * { color: var(--titulo) !important; }
.stApp [data-testid="stCaptionContainer"] p,
.stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricLabel"] * { color: var(--texto-suave) !important; }
.stApp button[data-baseweb="tab"] p { color: var(--texto-suave); }
.stApp button[data-baseweb="tab"][aria-selected="true"] p { color: var(--titulo); }
.stApp hr { border-color: var(--borda); }

/* ---------- Campos ---------- */
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"], .stApp [data-baseweb="textarea"],
.stApp [data-baseweb="select"] > div,
[data-baseweb="input"] input, [data-baseweb="base-input"] input, .stApp textarea {
  background-color: var(--campo) !important;
  color: var(--texto) !important;
}
.stApp [data-baseweb="input"], .stApp [data-baseweb="textarea"], .stApp [data-baseweb="select"] > div {
  border-color: var(--borda);
}
[data-baseweb="select"] div, [data-baseweb="select"] span { color: var(--texto); }
[data-baseweb="select"] svg, [data-baseweb="input"] svg { fill: var(--texto-suave); }
.stApp ::placeholder { color: var(--texto-suave) !important; -webkit-text-fill-color: var(--texto-suave) !important; opacity: 1; }

/* ---------- Listas suspensas, calendário, menu ⋮ e janelas (ficam fora do .stApp) ---------- */
[data-baseweb="popover"] > div, [data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul,
[data-baseweb="calendar"] {
  background-color: var(--superficie) !important;
  color: var(--texto) !important;
}
[data-baseweb="popover"] li, [data-baseweb="popover"] li *, [data-baseweb="calendar"] * { color: var(--texto) !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] {
  background-color: var(--borda) !important;
}
[data-testid="stDialog"] [role="dialog"] { background-color: var(--superficie); }

/* ---------- Botões ---------- */
.stApp [data-testid="stBaseButton-primary"], .stApp [data-testid="stBaseButton-primaryFormSubmit"],
.stApp button[kind="primary"], .stApp button[kind="primaryFormSubmit"] {
  background-color: var(--laranja) !important;
  border-color: var(--laranja) !important;
}
.stApp [data-testid="stBaseButton-primary"]:hover, .stApp [data-testid="stBaseButton-primaryFormSubmit"]:hover,
.stApp button[kind="primary"]:hover, .stApp button[kind="primaryFormSubmit"]:hover {
  background-color: var(--btn-hover) !important;
  border-color: var(--btn-hover) !important;
}
.stApp [data-testid="stBaseButton-primary"] *, .stApp [data-testid="stBaseButton-primaryFormSubmit"] *,
.stApp button[kind="primary"] *, .stApp button[kind="primaryFormSubmit"] * { color: var(--roxo-900) !important; }

.stApp [data-testid="stBaseButton-secondary"], .stApp [data-testid="stBaseButton-secondaryFormSubmit"],
.stApp button[kind="secondary"], .stApp button[kind="secondaryFormSubmit"] {
  background-color: var(--superficie);
  border-color: var(--borda);
}
.stApp [data-testid="stBaseButton-secondary"]:hover, .stApp [data-testid="stBaseButton-secondaryFormSubmit"]:hover,
.stApp button[kind="secondary"]:hover, .stApp button[kind="secondaryFormSubmit"]:hover {
  border-color: var(--laranja);
}

/* ---------- Superfícies, tabelas e avisos ---------- */
[data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--borda); }
[data-testid="stExpander"] details { background-color: var(--superficie); border-color: var(--borda); }

/* A tabela é um canvas (o CSS não alcança): inverte as cores por filtro e gira o matiz de volta. */
[data-testid="stDataFrame"] {
  border-color: var(--borda-tabela);
  filter: invert(.88) hue-rotate(180deg);
}
"""

def css_tema(modo: str) -> str:
    """CSS completo do tema pedido ("claro" ou "escuro"); qualquer outro valor cai no claro."""
    return CSS + CSS_ESCURO if modo == "escuro" else CSS

# Tela de entrada: sem menu lateral e com o painel laranja de boas-vindas.
CSS_LOGIN = """
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {
  display: none !important;
}
.block-container, [data-testid="stMainBlockContainer"] { max-width: 1080px; padding-top: 4rem; }

/* Cartão do formulário (E-mail ... Entrar). Estiliza o bloco da coluna que contém as abas, o que funciona em
   qualquer versão do Streamlit; a moldura nativa do st.container(border=True) é neutralizada para não duplicar. */
[data-testid="stMain"] [data-testid="stColumn"]:has([data-baseweb="tab-list"]) > *:first-child,
[data-testid="stMain"] [data-testid="column"]:has([data-baseweb="tab-list"]) > *:first-child {
  background: var(--superficie) !important;
  border: 2px solid var(--borda-forte) !important;
  border-radius: 16px !important;
  padding: 1.5rem 1.75rem 1.75rem !important;
  box-shadow: 0 6px 22px var(--sombra);
}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}

.atila-hero {
  min-height: 27rem;
  padding: 2.5rem 2.25rem;
  border-radius: 16px;
  background: var(--hero-fundo);
  color: var(--hero-texto);
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}
.atila-hero__logo {
  width: 3.2rem; height: 3.2rem;
  display: grid; place-items: center;
  border-radius: 14px;
  background: var(--hero-logo-fundo);
  color: var(--hero-logo-texto);
  font: 800 1.7rem/1 var(--fonte-titulo);
}
.atila-hero__titulo { font: 800 2.6rem/1.05 var(--fonte-titulo); }
.atila-hero__texto { font-size: 1.1rem; font-weight: 600; line-height: 1.45; max-width: 26rem; margin: 0; }
.atila-hero__lista { margin: auto 0 0; padding: 0; list-style: none; display: grid; gap: .6rem; }
.atila-hero__lista li {
  padding-left: 1.1rem;
  border-left: 4px solid var(--hero-traco);
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
