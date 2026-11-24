"""Dashboard — usa EXATAMENTE os mesmos controllers/Firestore das abas Salas e Agendamentos."""
import streamlit as st

from controllers import agendamento_controller, sala_controller, usuario_controller
from utils import firestore_client as fs
from utils import tempo
from utils.auth import somente_admin, usuario_atual
from views.layout import carregar


def obter_dados() -> dict:
    """Lê tudo do Firestore (sem cache) e devolve métricas + tabelas prontas."""
    salas = sala_controller.listar()
    reservas = agendamento_controller.listar()
    usuarios = usuario_controller.listar()

    status = reservas["status"]
    hoje = str(tempo.hoje())
    futuras = reservas[status.isin(agendamento_controller.STATUS_ATIVOS) & (reservas["data"].astype(str) >= hoje)]

    visao = salas.copy()
    visao["reservas_ativas"] = visao["sala"].astype(str).map(
        futuras["sala"].astype(str).value_counts()
    ).fillna(0).astype(int)

    # Só aulas de hoje em diante: quando o dia passa, a reserva sai daqui sozinha (é filtro de exibição,
    # calculado a cada carga — nada é gravado nem apagado; o registro segue em Agendamentos > Histórico).
    # Reprovadas também ficam de fora da visão principal.
    recentes = reservas[(status != "Reprovada") & (reservas["data"].astype(str) >= hoje)]
    recentes = recentes.sort_values("criado_em", ascending=False).head(10)

    pendentes_por_vir = int(((status == "Pendente") & (reservas["data"].astype(str) >= hoje)).sum())

    nomes_salas = set(salas["sala"].astype(str))
    orfas = reservas[~reservas["sala"].astype(str).isin(nomes_salas)]

    return {
        "salas": salas,
        "reservas": reservas,
        "usuarios": usuarios,
        "visao_salas": visao,
        "recentes": recentes,
        "reservas_orfas": orfas,
        "pendentes_por_vir": pendentes_por_vir,
        "metricas": {
            "Salas": len(salas),
            "Reservas": len(reservas),
            "Confirmadas": int((status == "Confirmada").sum()),
            "Pendentes": int((status == "Pendente").sum()),
            "Usuários": len(usuarios),
        },
    }


def dashboard():
    """Admin: painel completo. Professor: início enxuto com as próprias reservas."""
    if somente_admin():
        dashboard_admin()
    else:
        dashboard_professor()


def obter_dados_professor(usuario: dict) -> dict:
    minhas = agendamento_controller.classificar(
        agendamento_controller.do_usuario(agendamento_controller.listar(), usuario)
    )
    proximas = minhas[minhas["aba"] == "Aprovados"].sort_values(["data", "inicio"]).head(5)
    pendentes = minhas[minhas["aba"] == "Pendentes"].sort_values(["data", "inicio"])
    return {
        "minhas": minhas,
        "proximas": proximas,
        "pendentes": pendentes,
        "metricas": {
            "Pendentes": len(pendentes),
            "Aprovadas (próximas)": int((minhas["aba"] == "Aprovados").sum()),
            "Realizadas": int((minhas["situacao"] == "Concluída").sum()),
        },
    }


def dashboard_professor():
    usuario = usuario_atual()
    st.title(f"Olá, {usuario['nome'].split()[0] if usuario['nome'].strip() else 'professor(a)'}!")
    st.caption("Solicite salas, acompanhe suas reservas e consulte a disponibilidade.")
    c1, c2, c3 = st.columns(3)
    c1.page_link("pages/2_Nova_Reserva.py", label="Solicitar reserva", icon="📝")
    c2.page_link("pages/7_Minhas_Reservas.py", label="Minhas reservas", icon="📅")
    c3.page_link("pages/8_Disponibilidade.py", label="Disponibilidade das salas", icon="🔎")
    st.divider()

    d = carregar(obter_dados_professor, usuario)
    cols = st.columns(len(d["metricas"]))
    for col, (rotulo, valor) in zip(cols, d["metricas"].items()):
        col.metric(rotulo, valor)

    cols_tab = ["data", "inicio", "fim", "sala", "disciplina", "situacao"]
    st.subheader("Próximas reservas aprovadas")
    if d["proximas"].empty:
        st.info("Você não tem reservas aprovadas por vir.")
    else:
        st.dataframe(d["proximas"][cols_tab], use_container_width=True, hide_index=True)
    if not d["pendentes"].empty:
        st.subheader("Aguardando aprovação")
        st.dataframe(d["pendentes"][cols_tab], use_container_width=True, hide_index=True)


def dashboard_admin():
    topo1, topo2 = st.columns([5, 1], vertical_alignment="center")
    topo1.title("Dashboard")
    topo1.caption("Visão geral de salas, reservas e usuários.")
    if topo2.button("Atualizar", icon=":material/refresh:", use_container_width=True):
        st.rerun()

    d = carregar(obter_dados)

    if somente_admin() and fs.modo_conexao() == "api_key":
        st.warning(
            "O app está no modo legado (API key), que exige regras do Firestore abertas ao público. "
            "Configure [gcp_service_account] nos Secrets e feche as regras (veja o README)."
        )

    cols = st.columns(len(d["metricas"]))
    for col, (rotulo, valor) in zip(cols, d["metricas"].items()):
        col.metric(rotulo, valor)

    if d["pendentes_por_vir"]:
        a1, a2 = st.columns([4, 1], vertical_alignment="center")
        a1.info(f"{d['pendentes_por_vir']} solicitação(ões) de reserva aguardando sua análise.")
        a2.page_link("pages/3_Agendamentos.py", label="Analisar", icon="📅")

    if not d["reservas_orfas"].empty:
        nomes = ", ".join(sorted(set(d["reservas_orfas"]["sala"].astype(str))))
        st.warning(f"Há reservas apontando para salas que não estão cadastradas: {nomes}.")

    st.subheader("Visão geral das salas")
    if d["visao_salas"].empty:
        st.info("Nenhuma sala cadastrada.")
    else:
        mostrar = d["visao_salas"].rename(columns={"reservas_ativas": "reservas ativas (hoje em diante)"})
        st.dataframe(mostrar, use_container_width=True, hide_index=True)

    st.subheader("Agendamentos recentes")
    st.caption("Mostra só aulas de hoje em diante. Dias que já passaram saem daqui automaticamente "
               "e ficam no Histórico da página Agendamentos.")
    if d["reservas"].empty:
        st.info("Nenhum agendamento cadastrado.")
    elif d["recentes"].empty:
        st.info("Nenhum agendamento de hoje em diante.")
    else:
        cols_tab = ["id", "professor", "disciplina", "sala", "data", "inicio", "fim", "status"]
        st.dataframe(d["recentes"][cols_tab], use_container_width=True, hide_index=True)
