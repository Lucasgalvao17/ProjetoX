"""Executa as páginas reais (app.py e pages/*.py) com um Streamlit falso + Firestore falso."""
import runpy
import unittest
from datetime import date, datetime, time, timedelta
from unittest import mock

from utils import tempo
from tests.test_atila import Base, AMANHA, ag, auth, dc, fs, sala, sc, st, RAIZ, reserva, uc

ADMIN, PROF = "admin", "prof"
PAGINAS_ADMIN = ("pages/1_Salas.py", "pages/3_Agendamentos.py", "pages/4_Usuarios.py", "pages/5_Disciplinas.py")


def conta(email):
    """Conta REAL do Firestore: a sessão é revalidada contra o banco a cada página."""
    uc.garantir_usuarios_iniciais()
    d = uc.obter_por_email(email)
    return {"id": d["id"], "nome": d["nome"], "email": d["email"], "perfil": d["perfil"]}


def disc(codigo):
    return dc.listar().set_index("codigo").loc[codigo, "id"]


def rodar(arquivo, entradas=None, usuario=ADMIN):
    st.resetar(entradas)
    st.session_state.clear()
    if usuario == ADMIN:
        usuario = conta("admin@atila.local")
    elif usuario == PROF:
        usuario = conta("ana@atila.local")
    st.session_state.clear()
    if usuario:
        st.session_state["usuario"] = dict(usuario)
    desfecho = None
    try:
        runpy.run_path(str(RAIZ / arquivo), run_name="__main__")
    except st.StopExecution:
        desfecho = "stop/rerun"
    except st.SwitchPage as e:
        desfecho = f"switch:{e.destino}"
    texto = [f"{t}: {x}" for t, x in st.SAIDA]
    return desfecho, texto, list(st.DADOS["lista"])


def contem(texto, trecho):
    return any(trecho in linha for linha in texto)


def avisos():
    return [t for _, t in st.session_state.get("_avisos", [])]


def menu(saida):
    return [l.split(": ", 1)[1] for l in saida if l.startswith("menu: ")]


def reserva_pg(**kw):
    return {"Quantidade de alunos": 30, "Data": tempo.hoje() + timedelta(days=1), "Solicitar reserva": True,
            "Disciplina": disc("WEB101"), **kw}


class TestAcessoEMenuPorPerfil(Base):
    def test_sem_login_redireciona(self):
        for pg in ("app.py", "pages/2_Nova_Reserva.py", "pages/7_Minhas_Reservas.py", "pages/8_Disponibilidade.py",
                   "pages/6_Perfil.py", *PAGINAS_ADMIN):
            d, _, _ = rodar(pg, usuario=None)
            self.assertEqual(d, "switch:pages/0_Login.py", pg)

    def test_menu_do_professor_e_enxuto(self):
        _, saida, _ = rodar("app.py", usuario=PROF)
        m = menu(saida)
        self.assertEqual(m, ["app.py", "pages/2_Nova_Reserva.py", "pages/7_Minhas_Reservas.py",
                             "pages/8_Disponibilidade.py", "pages/6_Perfil.py"])

    def test_menu_do_admin_e_completo(self):
        _, saida, _ = rodar("app.py")
        m = set(menu(saida))
        for pg in (*PAGINAS_ADMIN, "pages/2_Nova_Reserva.py", "pages/8_Disponibilidade.py", "pages/6_Perfil.py", "app.py"):
            self.assertIn(pg, m)
        self.assertNotIn("pages/7_Minhas_Reservas.py", m)

    def test_professor_nao_acessa_paginas_de_admin(self):
        for pg in PAGINAS_ADMIN:
            d, saida, tabelas = rodar(pg, usuario=PROF)
            self.assertEqual(d, "stop/rerun", pg)
            self.assertTrue(contem(saida, "restrita ao administrador"), pg)
            self.assertEqual(tabelas, [], pg)               # nada foi exibido

    def test_usuario_desativado_perde_a_sessao_na_hora(self):
        p = conta("ana@atila.local")
        uc.definir_ativo(p["id"], "Não")
        st.resetar(); st.session_state.clear(); st.session_state["usuario"] = dict(p)
        d = None
        try:
            runpy.run_path(str(RAIZ / "app.py"), run_name="__main__")
        except st.SwitchPage as e:
            d = e.destino
        self.assertEqual(d, "pages/0_Login.py")
        self.assertNotIn("usuario", st.session_state)

    def test_mudanca_de_perfil_vale_na_proxima_pagina(self):
        p = conta("ana@atila.local")
        uc.atualizar(p["id"], p["nome"], "Administrador")
        d, saida, _ = rodar("pages/3_Agendamentos.py", usuario=p)      # sessão ainda diz "Professor"
        self.assertFalse(contem(saida, "restrita ao administrador"))


class TestDashboard(Base):
    def test_dashboard_admin_mostra_dados_reais(self):
        sc.cadastrar(sala("Sala Real A", cap=50)); sc.cadastrar(sala("Sala Real B", cap=20))
        rid = ag.criar(reserva("Sala Real A", prof="Maria"))
        ag.alterar_status(rid, "Confirmada")
        d, saida, tabelas = rodar("app.py")
        self.assertIsNone(d)
        for esperado in ("Salas=2", "Reservas=1", "Confirmadas=1", "Pendentes=0", "Usuários=2"):
            self.assertTrue(contem(saida, esperado), (esperado, saida))
        visao, recentes = tabelas
        self.assertEqual(set(visao["sala"]), {"Sala Real A", "Sala Real B"})
        self.assertEqual(recentes.iloc[0]["professor"], "Maria")

    def test_reprovadas_nao_aparecem_em_recentes_mas_continuam_no_banco(self):
        a = ag.criar(reserva(prof="Reprovado")); ag.alterar_status(a, "Reprovada")
        ag.criar(reserva(ini="18:00", fim="19:00", prof="Pendente")); sc.cadastrar(sala("Sala 101"))
        _, saida, tabelas = rodar("app.py")
        self.assertEqual(tabelas[1]["professor"].tolist(), ["Pendente"])
        self.assertTrue(contem(saida, "Reservas=2"))

    def test_dashboard_vazio(self):
        _, saida, _ = rodar("app.py")
        self.assertTrue(contem(saida, "Nenhuma sala cadastrada"))
        self.assertTrue(contem(saida, "Nenhum agendamento cadastrado"))

    def test_firestore_fora_mostra_erro_e_para(self):
        con = fs._conexao()
        with mock.patch.object(con.sessao, "request", side_effect=ConnectionError("x")):
            d, saida, _ = rodar("app.py", usuario=None)
        self.assertEqual(d, "switch:pages/0_Login.py")     # sem sessão nem chega a ler
        with mock.patch.object(con.sessao, "request", side_effect=ConnectionError("x")):
            st.resetar(); st.session_state.clear()
            st.session_state["usuario"] = {"id": "x", "nome": "A", "email": "a@a", "perfil": "Administrador"}
            try:
                runpy.run_path(str(RAIZ / "app.py"), run_name="__main__")
            except st.StopExecution:
                pass
        self.assertTrue(contem([f"{t}: {x}" for t, x in st.SAIDA], "Não foi possível acessar o Firestore"))

    def test_inicio_do_professor_mostra_so_as_reservas_dele(self):
        sc.cadastrar(sala("Sala 101"))
        ana = conta("ana@atila.local")
        a = ag.criar({**reserva(prof="Ana Souza"), "criado_por": ana["email"]}); ag.alterar_status(a, "Confirmada")
        ag.criar({**reserva(ini="18:00", fim="19:00", prof="Ana Souza"), "criado_por": ana["email"]})
        ag.criar({**reserva(ini="08:00", fim="09:00", prof="Outro"), "criado_por": "outro@x.com"})
        d, saida, tabelas = rodar("app.py", usuario=PROF)
        self.assertIsNone(d)
        for esperado in ("Pendentes=1", "Aprovadas (próximas)=1"):
            self.assertTrue(contem(saida, esperado), (esperado, saida))
        self.assertFalse(contem(saida, "Usuários="))        # sem métricas de gestão
        self.assertEqual(len(tabelas[0]), 1)
        self.assertNotIn("Outro", "".join(t.to_string() for t in tabelas))


class TestSalasEdicao(Base):
    def _editar(self, sid, **novos):
        base = {"editar_sala_sel": sid}
        base.update({f"ed_{c}_{sid}": v for c, v in novos.items()})
        base["Salvar alterações"] = True
        return rodar("pages/1_Salas.py", base)

    def test_editar_salva_no_firestore_e_a_tela_recarrega(self):
        sid = sc.cadastrar(sala("Sala 101", cap=40))
        d, _, _ = self._editar(sid, sala="Sala 101 (reformada)", capacidade=55, tipo="Auditório", projetor="Não")
        self.assertEqual(d, "stop/rerun")                                 # st.rerun() após salvar
        gravada = fs.obter("salas", sid)
        self.assertEqual((gravada["sala"], gravada["capacidade"], gravada["tipo"], gravada["projetor"]),
                         ("Sala 101 (reformada)", 55, "Auditório", "Não"))
        self.assertTrue(any("Sala atualizada" in a for a in avisos()))
        _, _, tabelas = rodar("pages/1_Salas.py")
        self.assertIn("Sala 101 (reformada)", tabelas[0]["sala"].tolist())

    def test_renomear_atualiza_as_reservas_da_sala(self):
        sid = sc.cadastrar(sala("Sala 101")); sc.cadastrar(sala("Sala 102"))
        r1 = ag.criar(reserva("Sala 101")); r2 = ag.criar(reserva("Sala 102"))
        ag.alterar_status(r1, "Cancelada")                                 # inclui reservas não ativas
        self._editar(sid, sala="Bloco A - 101")
        nomes = dict(zip(ag.listar()["id"], ag.listar()["sala"]))
        self.assertEqual((nomes[r1], nomes[r2]), ("Bloco A - 101", "Sala 102"))
        self.assertTrue(any("1 reserva(s) foram atualizadas" in a for a in avisos()))
        self.assertEqual(dash_orfas(), 0)

    def test_nome_duplicado_na_edicao_e_recusado_sem_efeitos(self):
        sid = sc.cadastrar(sala("Sala 101")); sc.cadastrar(sala("Sala 102"))
        r = ag.criar(reserva("Sala 101"))
        _, saida, _ = self._editar(sid, sala="sala 102")
        self.assertTrue(contem(saida, "Já existe outra sala"))
        self.assertEqual(fs.obter("salas", sid)["sala"], "Sala 101")
        self.assertEqual(fs.obter("reservas", r)["sala"], "Sala 101")

    def test_manter_o_proprio_nome_nao_e_duplicata(self):
        sid = sc.cadastrar(sala("Sala 101", cap=40))
        self.assertEqual(sc.atualizar(sid, {"sala": "Sala 101", "capacidade": 60}), 0)
        self.assertEqual(fs.obter("salas", sid)["capacidade"], 60)

    def test_falha_no_meio_da_renomeacao_nao_altera_a_sala_e_repetir_conclui(self):
        sid = sc.cadastrar(sala("Sala 101"))
        r1 = ag.criar(reserva("Sala 101")); r2 = ag.criar(reserva("Sala 101", ini="18:00", fim="19:00"))
        original, chamadas = fs.atualizar, {"n": 0}

        def quebra_na_segunda(colecao, doc_id, campos):
            if colecao == "reservas":
                chamadas["n"] += 1
                if chamadas["n"] == 2:
                    raise fs.FirestoreError("falha simulada")
            return original(colecao, doc_id, campos)

        with mock.patch.object(fs, "atualizar", quebra_na_segunda):
            with self.assertRaises(fs.FirestoreError):
                sc.atualizar(sid, {"sala": "Nova"})
        self.assertEqual(fs.obter("salas", sid)["sala"], "Sala 101")        # sala intacta
        sc.atualizar(sid, {"sala": "Nova"})                                  # repetir conclui
        self.assertEqual(set(ag.listar()["sala"]), {"Nova"})
        self.assertEqual(fs.obter("salas", sid)["sala"], "Nova")

    def test_formulario_traz_os_valores_atuais(self):
        sid = sc.cadastrar(sala("Sala 101", cap=77, tipo="Auditório"))
        # sem alterar nada e salvando: nada muda (prova que os valores iniciais vieram da sala)
        self._editar(sid)
        g = fs.obter("salas", sid)
        self.assertEqual((g["sala"], g["capacidade"], g["tipo"]), ("Sala 101", 77, "Auditório"))

    def test_dados_antigos_fora_do_intervalo_nao_quebram_o_formulario(self):
        sid = fs.criar("salas", {"sala": "Velha", "capacidade": 900, "andar": 99, "computadores": "abc"})["id"]
        d, saida, _ = rodar("pages/1_Salas.py", {"editar_sala_sel": sid})
        self.assertFalse(any(l.startswith("error:") for l in saida), saida)

    def test_cadastro_duplicado_e_exclusao_bloqueada(self):
        sid = sc.cadastrar(sala("Sala 101")); ag.criar(reserva())
        _, saida, _ = rodar("pages/1_Salas.py", {"Nome da sala": "sala 101", "Cadastrar sala": True})
        self.assertTrue(contem(saida, "Já existe uma sala"))
        _, saida, _ = rodar("pages/1_Salas.py", {"Excluir sala": True, "Sala para excluir": sid})
        self.assertTrue(contem(saida, "reserva(s) pendente(s)/confirmada(s)"), saida)
        self.assertEqual(len(sc.listar()), 1)


def dash_orfas():
    from controllers import dashboard_controller as dash
    return len(dash.obter_dados()["reservas_orfas"])


class TestAgendamentosQuatroTabelas(Base):
    def test_classificacao_nas_quatro_abas(self):
        agora = datetime(2026, 11, 20, 12, 0)
        ag.criar(reserva(data="2026-11-25", prof="Aprovada futura"))                         # será confirmada
        ag.criar(reserva(data="2026-11-26", prof="Pendente"))
        ag.criar(reserva(data="2026-11-27", prof="Cancelada"))
        ag.criar(reserva(data="2026-11-28", prof="Reprovada"))
        ag.criar(reserva(data="2026-11-10", prof="Aprovada já realizada"))
        ids = dict(zip(ag.listar()["professor"], ag.listar()["id"]))
        ag.alterar_status(ids["Aprovada futura"], "Confirmada"); ag.alterar_status(ids["Aprovada já realizada"], "Confirmada")
        ag.alterar_status(ids["Cancelada"], "Cancelada"); ag.alterar_status(ids["Reprovada"], "Reprovada", "adm", "Sem vaga")
        df = ag.classificar(ag.listar(), agora)
        por_aba = {a: sorted(df[df["aba"] == a]["professor"]) for a in ag.ABAS}
        self.assertEqual(por_aba, {"Aprovados": ["Aprovada futura"], "Pendentes": ["Pendente"],
                                   "Cancelados": ["Cancelada"], "Histórico": ["Aprovada já realizada", "Reprovada"]})
        self.assertEqual(df.set_index("professor").loc["Aprovada já realizada", "situacao"], "Concluída")

    def test_reprovar_mantem_o_registro_com_motivo_e_tira_da_visao_principal(self):
        sc.cadastrar(sala("Sala 101"))
        rid = ag.criar(reserva())
        d, _, _ = rodar("pages/3_Agendamentos.py", {"btn_reprovar": True, "sel_pendentes": rid, "motivo_pendentes": "Sala em obra"})
        self.assertEqual(d, "stop/rerun")
        doc = fs.obter("reservas", rid)                                       # NÃO foi apagado
        self.assertEqual((doc["status"], doc["motivo"], doc["atualizado_por"]), ("Reprovada", "Sala em obra", "admin@atila.local"))
        self.assertTrue(any("mantido no Histórico" in a for a in avisos()))
        _, saida, tabelas = rodar("pages/3_Agendamentos.py")
        self.assertTrue(contem(saida, "Pendentes: 0"), saida)
        self.assertTrue(contem(saida, "Histórico: 1"), saida)
        self.assertEqual(len(tabelas), 1)                                      # só a tabela do Histórico é exibida
        self.assertEqual(tabelas[0].iloc[0]["situacao"], "Reprovada")
        self.assertEqual(tabelas[0].iloc[0]["motivo"], "Sala em obra")

    def test_reprovada_libera_o_horario_para_outra_reserva(self):
        rid = ag.criar(reserva()); ag.alterar_status(rid, "Reprovada")
        ag.criar(reserva(prof="Outro"))

    def test_aprovar_e_cancelar_pelo_admin(self):
        rid = ag.criar(reserva())
        rodar("pages/3_Agendamentos.py", {"btn_aprovar": True, "sel_pendentes": rid})
        self.assertEqual(fs.obter("reservas", rid)["status"], "Confirmada")
        rodar("pages/3_Agendamentos.py", {"btn_cancelar": True, "sel_aprovados": rid, "motivo_aprovados": "Greve"})
        d = fs.obter("reservas", rid)
        self.assertEqual((d["status"], d["motivo"]), ("Cancelada", "Greve"))

    def test_reabrir_reprovada_revalida_conflito(self):
        a = ag.criar(reserva(prof="A")); ag.alterar_status(a, "Reprovada")
        ag.criar(reserva(prof="B"))                                            # outro ocupou o horário
        _, saida, _ = rodar("pages/3_Agendamentos.py", {"btn_reabrir_historico": True, "sel_historico": a})
        self.assertTrue(contem(saida, "conflito de horário"), saida)
        self.assertEqual(fs.obter("reservas", a)["status"], "Reprovada")

    def test_reabrir_reprovada_quando_livre(self):
        a = ag.criar(reserva()); ag.alterar_status(a, "Reprovada", motivo="x")
        rodar("pages/3_Agendamentos.py", {"btn_reabrir_historico": True, "sel_historico": a})
        d = fs.obter("reservas", a)
        self.assertEqual((d["status"], d["motivo"]), ("Pendente", ""))         # motivo antigo limpo

    def test_reservas_ja_realizadas_nao_oferecem_reabertura(self):
        rid = ag.criar(reserva(data=str(tempo.hoje() - timedelta(days=3)))) if False else fs.criar(
            "reservas", reserva(data=str(tempo.hoje() - timedelta(days=3)), status="Confirmada"))["id"]
        _, saida, _ = rodar("pages/3_Agendamentos.py")
        self.assertTrue(contem(saida, "já realizadas não podem ser reabertas"), saida)


class TestProfessor(Base):
    def test_minhas_reservas_so_as_proprias_em_4_abas(self):
        ana = conta("ana@atila.local")
        a = ag.criar({**reserva(prof="Ana Souza"), "criado_por": ana["email"]})
        b = ag.criar({**reserva(ini="18:00", fim="19:00", prof="Ana Souza"), "criado_por": ana["email"]})
        ag.alterar_status(b, "Reprovada", "adm", "Sem sala")
        ag.criar({**reserva(ini="08:00", fim="09:00", prof="Outro"), "criado_por": "outro@x.com"})
        _, saida, tabelas = rodar("pages/7_Minhas_Reservas.py", usuario=PROF)
        for aba in ("Aprovados: 0", "Pendentes: 1", "Cancelados: 0", "Histórico: 1"):
            self.assertTrue(contem(saida, aba), (aba, saida))
        todos = "".join(t.to_string() for t in tabelas)
        self.assertNotIn("Outro", todos)
        self.assertIn("Sem sala", todos)                                        # motivo visível para o professor
        self.assertNotIn("criado_por", "".join(c for t in tabelas for c in t.columns))

    def test_professor_cancela_a_propria_e_nao_a_alheia(self):
        ana = conta("ana@atila.local")
        minha = ag.criar({**reserva(prof="Ana Souza"), "criado_por": ana["email"]})
        alheia = ag.criar({**reserva(ini="18:00", fim="19:00", prof="Outro"), "criado_por": "outro@x.com"})
        rodar("pages/7_Minhas_Reservas.py", {"btn_cancelar_pendentes": True, "sel_pendentes": minha}, usuario=PROF)
        self.assertEqual(fs.obter("reservas", minha)["status"], "Cancelada")
        with self.assertRaises(ValueError):
            ag.cancelar_propria(alheia, ana["email"])
        self.assertEqual(fs.obter("reservas", alheia)["status"], "Pendente")

    def test_nao_cancela_reserva_ja_realizada_nem_reprovada(self):
        ana = conta("ana@atila.local")
        passada = fs.criar("reservas", {**reserva(data=str(tempo.hoje() - timedelta(days=2)), status="Confirmada"), "criado_por": ana["email"]})["id"]
        with self.assertRaises(ValueError):
            ag.cancelar_propria(passada, ana["email"])
        rep = ag.criar({**reserva(), "criado_por": ana["email"]}); ag.alterar_status(rep, "Reprovada")
        with self.assertRaises(ValueError):
            ag.cancelar_propria(rep, ana["email"])

    def test_minhas_reservas_vazio(self):
        _, saida, _ = rodar("pages/7_Minhas_Reservas.py", usuario=PROF)
        self.assertTrue(contem(saida, "ainda não fez nenhuma solicitação"))

    def test_reservas_antigas_sem_criado_por_casam_pelo_nome(self):
        fs.criar("reservas", {**reserva(prof="Ana Souza"), "criado_por": ""})
        _, _, tabelas = rodar("pages/7_Minhas_Reservas.py", usuario=PROF)
        self.assertEqual(len(tabelas), 1)

    def test_disponibilidade_livre_ocupada_e_privacidade(self):
        sc.cadastrar(sala("Sala 101", cap=40)); sc.cadastrar(sala("Sala 102", cap=10))
        ag.criar(reserva("Sala 101", prof="Fulano Secreto"))
        base = {"disp_data": tempo.hoje() + timedelta(days=1)}
        _, saida, tabelas = rodar("pages/8_Disponibilidade.py", base, usuario=PROF)
        disp = dict(zip(tabelas[0]["sala"], tabelas[0]["disponibilidade"]))
        self.assertEqual(disp, {"Sala 101": "Ocupada", "Sala 102": "Livre"})
        self.assertTrue(contem(saida, "Salas livres no horário=1"))
        self.assertNotIn("Fulano Secreto", "".join(t.to_string() for t in tabelas))       # professor não vê nomes
        _, _, tabelas_admin = rodar("pages/8_Disponibilidade.py", base)
        self.assertIn("Fulano Secreto", tabelas_admin[-1].to_string())                    # admin vê

    def test_disponibilidade_filtros_e_intervalo_invalido(self):
        sc.cadastrar(sala("Pequena", cap=10)); sc.cadastrar(sala("Grande", cap=80, tipo="Auditório"))
        _, _, t = rodar("pages/8_Disponibilidade.py", {"disp_cap": 50}, usuario=PROF)
        self.assertEqual(t[0]["sala"].tolist(), ["Grande"])
        _, _, t = rodar("pages/8_Disponibilidade.py", {"disp_tipo": "Auditório"}, usuario=PROF)
        self.assertEqual(t[0]["sala"].tolist(), ["Grande"])
        _, saida, _ = rodar("pages/8_Disponibilidade.py", {"disp_fim": time(9, 0), "disp_inicio": time(10, 0)}, usuario=PROF)
        self.assertTrue(contem(saida, "horário final deve ser posterior"))

    def test_disponibilidade_so_livres(self):
        sc.cadastrar(sala("A")); sc.cadastrar(sala("B"))
        ag.criar(reserva("A"))
        _, _, t = rodar("pages/8_Disponibilidade.py", {"disp_data": tempo.hoje() + timedelta(days=1), "disp_livres": True}, usuario=PROF)
        self.assertEqual(t[0]["sala"].tolist(), ["B"])


class TestNovaReserva(Base):
    def test_disciplina_e_selecionada_do_firestore_e_gravada_com_id(self):
        sc.cadastrar(sala("Lab 7", cap=35))
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", reserva_pg(), usuario=PROF)
        self.assertTrue(contem(saida, "Reserva enviada"), saida)
        r = ag.listar().iloc[0]
        self.assertEqual((r["disciplina"], r["disciplina_id"]), ("Programação Web", disc("WEB101")))
        self.assertEqual((r["professor"], r["criado_por"]), ("Ana Souza", "ana@atila.local"))   # professor reserva em nome próprio

    def test_professor_nao_consegue_reservar_em_nome_de_outro(self):
        sc.cadastrar(sala("Lab 7"))
        rodar("pages/2_Nova_Reserva.py", reserva_pg(**{"Professor / solicitante": "Fulano"}), usuario=PROF)
        self.assertEqual(ag.listar().iloc[0]["professor"], "Ana Souza")

    def test_admin_pode_reservar_em_nome_de_outro(self):
        sc.cadastrar(sala("Lab 7"))
        rodar("pages/2_Nova_Reserva.py", reserva_pg(**{"Professor / solicitante": "Fulano"}))
        self.assertEqual(ag.listar().iloc[0]["professor"], "Fulano")

    def test_disciplina_inativa_some_da_lista_e_e_recusada_no_servidor(self):
        sc.cadastrar(sala("Lab 7"))
        did = disc("WEB101"); dc.atualizar(did, "Programação Web", "SI", "Não")
        with self.assertRaises(ValueError):
            ag.criar({**reserva(), "disciplina_id": did})
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", reserva_pg(Disciplina=did), usuario=PROF)
        self.assertFalse(contem(saida, "Reserva enviada"))
        self.assertTrue(ag.listar().empty)

    def test_disciplina_inexistente_e_recusada(self):
        with self.assertRaises(ValueError):
            ag.criar({**reserva(), "disciplina_id": "naoexiste"})

    def test_sem_disciplinas_ativas_orienta_cada_perfil(self):
        sc.cadastrar(sala("Lab 7"))
        for _, r in dc.listar().iterrows():
            dc.atualizar(r["id"], r["nome"], r["curso"], "Não")
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", usuario=PROF)
        self.assertTrue(contem(saida, "Peça ao administrador"))
        _, saida, _ = rodar("pages/2_Nova_Reserva.py")
        self.assertTrue(contem(saida, "Cadastre na página Disciplinas"))

    def test_sem_salas(self):
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", usuario=PROF)
        self.assertTrue(contem(saida, "Ainda não há salas"))

    def test_validacoes_de_data_e_horario(self):
        sc.cadastrar(sala("S1", cap=40))
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", reserva_pg(**{"Data": tempo.hoje() - timedelta(days=1), "Horário final": time(13, 0)}), usuario=PROF)
        self.assertTrue(contem(saida, "horário final deve ser posterior"))
        self.assertTrue(contem(saida, "não pode estar no passado"))
        self.assertTrue(ag.listar().empty)

    def test_horario_de_hoje_que_ja_passou_e_recusado(self):
        sc.cadastrar(sala("S1", cap=40))
        with mock.patch.object(tempo, "agora", return_value=datetime(2026, 11, 20, 15, 0)):
            _, saida, _ = rodar("pages/2_Nova_Reserva.py", reserva_pg(**{"Data": date(2026, 11, 20), "Horário inicial": time(14, 0), "Horário final": time(16, 0)}), usuario=PROF)
        self.assertTrue(contem(saida, "horário inicial de hoje já passou"), saida)

    def test_reserva_excepcional_exige_justificativa(self):
        sc.cadastrar(sala("Pequena", cap=10))
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", reserva_pg(), usuario=PROF)
        self.assertTrue(contem(saida, "exige justificativa"))
        self.assertTrue(contem(saida, "Informe a justificativa"))
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", reserva_pg(**{"Justificativa para reserva excepcional": "Evento"}), usuario=PROF)
        self.assertTrue(contem(saida, "Reserva enviada"))

    def test_recomendacao_melhor_encaixe(self):
        sc.cadastrar(sala("Grande", cap=200)); sc.cadastrar(sala("Media", cap=40)); sc.cadastrar(sala("Pequena", cap=10))
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", {"Quantidade de alunos": 30}, usuario=PROF)
        self.assertTrue(contem(saida, "**Media**"), saida)

    def test_fluxo_completo_sala_reserva_conflito_aprovacao_dashboard(self):
        rodar("pages/1_Salas.py", {"Nome da sala": "Lab 7", "Capacidade": 35, "Cadastrar sala": True})
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", reserva_pg(), usuario=PROF)
        self.assertTrue(contem(saida, "Reserva enviada"), saida)
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", reserva_pg(), usuario=PROF)
        self.assertTrue(contem(saida, "Conflito de horário"), saida)
        rid = ag.listar().iloc[0]["id"]
        rodar("pages/3_Agendamentos.py", {"btn_aprovar": True, "sel_pendentes": rid})
        _, saida, tabelas = rodar("app.py")
        for esperado in ("Salas=1", "Reservas=1", "Confirmadas=1"):
            self.assertTrue(contem(saida, esperado), (esperado, saida))
        self.assertEqual(tabelas[0].iloc[0]["reservas ativas (hoje em diante)"], 1)


class TestUsuariosPagina(Base):
    def test_admin_cria_usuario_que_consegue_logar(self):
        rodar("pages/4_Usuarios.py", {"novo_nome": "Prof Novo", "novo_email": "novo@x.com", "novo_senha": "abc12345",
                                      "novo_senha2": "abc12345", "novo_perfil": "Professor", "btn_criar_usuario": True})
        d = uc.obter_por_email("novo@x.com")
        self.assertEqual((d["nome"], d["perfil"], d["ativo"]), ("Prof Novo", "Professor", "Sim"))
        self.assertTrue(d["senha"].startswith("pbkdf2_sha256$"))                # nunca em texto puro
        st.session_state.clear()
        self.assertTrue(auth.login("novo@x.com", "abc12345"))
        self.assertTrue(fs.obter("usuarios", d["id"])["ultimo_login"])          # login registrado

    def test_admin_redefine_senha_e_a_antiga_deixa_de_valer(self):
        ana = conta("ana@atila.local")
        rodar("pages/4_Usuarios.py", {"senha_uid": ana["id"], "senha_nova": "novaSenha9", "senha_nova2": "novaSenha9", "btn_redefinir_senha": True})
        d = fs.obter("usuarios", ana["id"])
        self.assertEqual(d["senha_redefinida_por"], "admin@atila.local")
        self.assertTrue(d["senha_redefinida_em"])
        st.session_state.clear()
        self.assertFalse(auth.login("ana@atila.local", "ana123"))
        self.assertTrue(auth.login("ana@atila.local", "novaSenha9"))

    def test_redefinicao_valida_confirmacao_e_tamanho(self):
        ana = conta("ana@atila.local")
        _, saida, _ = rodar("pages/4_Usuarios.py", {"senha_uid": ana["id"], "senha_nova": "abcdef", "senha_nova2": "outra", "btn_redefinir_senha": True})
        self.assertTrue(contem(saida, "não coincidem"))
        _, saida, _ = rodar("pages/4_Usuarios.py", {"senha_uid": ana["id"], "senha_nova": "123", "senha_nova2": "123", "btn_redefinir_senha": True})
        self.assertTrue(contem(saida, "pelo menos 6"))
        self.assertTrue(auth.login("ana@atila.local", "ana123"))

    def test_admin_muda_perfil_e_desativa(self):
        ana = conta("ana@atila.local")
        rodar("pages/4_Usuarios.py", {"edit_uid": ana["id"], f"edit_nome_{ana['id']}": "Ana S.", f"edit_perfil_{ana['id']}": "Solicitante", "btn_salvar_usuario": True})
        d = fs.obter("usuarios", ana["id"]); self.assertEqual((d["nome"], d["perfil"]), ("Ana S.", "Solicitante"))
        rodar("pages/4_Usuarios.py", {"edit_uid": ana["id"], "btn_alternar_ativo": True})
        self.assertEqual(fs.obter("usuarios", ana["id"])["ativo"], "Não")
        rodar("pages/4_Usuarios.py", {"edit_uid": ana["id"], "btn_alternar_ativo": True})
        self.assertEqual(fs.obter("usuarios", ana["id"])["ativo"], "Sim")

    def test_admin_nao_se_desativa_nem_se_rebaixa(self):
        adm = conta("admin@atila.local")
        _, saida, _ = rodar("pages/4_Usuarios.py", {"edit_uid": adm["id"], "btn_alternar_ativo": True})
        self.assertTrue(contem(saida, "próprio usuário"))
        _, saida, _ = rodar("pages/4_Usuarios.py", {"edit_uid": adm["id"], f"edit_perfil_{adm['id']}": "Professor", "btn_salvar_usuario": True})
        self.assertTrue(contem(saida, "próprio usuário"))
        self.assertEqual(fs.obter("usuarios", adm["id"])["perfil"], "Administrador")

    def test_ultimo_admin_ativo_nao_pode_ser_removido_por_outro_admin(self):
        adm = conta("admin@atila.local"); ana = conta("ana@atila.local")
        uc.atualizar(ana["id"], ana["nome"], "Administrador")
        uc.definir_ativo(adm["id"], "Não", executor_id=ana["id"])              # há 2 admins: ok
        with self.assertRaises(ValueError):
            uc.definir_ativo(ana["id"], "Não", executor_id=adm["id"])         # restaria nenhum admin ativo
        with self.assertRaises(ValueError):
            uc.atualizar(ana["id"], ana["nome"], "Professor", executor_id=adm["id"])

    def test_lista_tem_perfil_status_e_ultimo_login_sem_senha(self):
        _, _, tabelas = rodar("pages/4_Usuarios.py")
        cols = set(tabelas[0].columns)
        self.assertTrue({"nome", "email", "perfil", "ativo", "criado_em", "ultimo_login"} <= cols)
        self.assertNotIn("senha", cols)

    def test_auto_cadastro_na_tela_de_login_vai_para_o_firestore(self):
        _, saida, _ = rodar("pages/0_Login.py", {"cad_nome": "N", "cad_email": "n@x.com", "cad_senha": "abcdef",
                                                 "cad_senha2": "abcdef", "Criar conta": True}, usuario=None)
        self.assertTrue(contem(saida, "Conta criada"))
        self.assertEqual(uc.obter_por_email("n@x.com")["ativo"], "Sim")

    def test_login_e_perfil(self):
        d, _, _ = rodar("pages/0_Login.py", {"login_email": "admin@atila.local", "login_senha": "admin123", "Entrar": True}, usuario=None)
        self.assertEqual(d, "switch:app.py")
        _, saida, _ = rodar("pages/0_Login.py", {"login_email": "admin@atila.local", "login_senha": "x", "Entrar": True}, usuario=None)
        self.assertTrue(contem(saida, "inválidos"))
        self.assertFalse(contem(saida, "admin123"))

    def test_perfil_alterar_senha_propria(self):
        _, saida, _ = rodar("pages/6_Perfil.py", {"pw_atual": "ana123", "pw_nova": "outra123", "pw_nova2": "outra123", "Alterar senha": True}, usuario=PROF)
        self.assertTrue(contem(saida, "Senha alterada"), saida)
        st.session_state.clear()
        self.assertTrue(auth.login("ana@atila.local", "outra123"))


class TestDisciplinasPagina(Base):
    def test_cadastro_pela_tela_e_duplicatas(self):
        _, _, t = rodar("pages/5_Disciplinas.py")
        self.assertEqual(len(t[0]), 3)
        rodar("pages/5_Disciplinas.py", {"Nome da disciplina": "Redes de Computadores", "Código": "red 401", "Curso": "SI", "Cadastrar disciplina": True})
        self.assertIn("RED401", dc.listar()["codigo"].tolist())                   # código normalizado
        for nome, codigo in (("Outra coisa", "RED401"), ("redes  de computadores!", "XYZ1"), ("REDES DE COMPUTADORES", "XYZ2")):
            _, saida, _ = rodar("pages/5_Disciplinas.py", {"Nome da disciplina": nome, "Código": codigo, "Cadastrar disciplina": True})
            self.assertTrue(contem(saida, "Já existe"), (nome, codigo, saida))
        self.assertEqual(len(dc.listar()), 4)

    def test_editar_e_desativar(self):
        did = disc("BD201")
        rodar("pages/5_Disciplinas.py", {"disc_edit_sel": did, f"disc_nome_{did}": "Banco de Dados I", f"disc_ativa_{did}": "Não", "Salvar alterações": True})
        g = fs.obter("disciplinas", did)
        self.assertEqual((g["nome"], g["ativa"], g["codigo"]), ("Banco de Dados I", "Não", "BD201"))
        self.assertNotIn(did, dc.listar_ativas()["id"].tolist())
        self.assertIn(did, dc.listar()["id"].tolist())                            # continua cadastrada

    def test_renomear_para_nome_de_outra_e_recusado(self):
        did = disc("BD201")
        _, saida, _ = rodar("pages/5_Disciplinas.py", {"disc_edit_sel": did, f"disc_nome_{did}": "programacao web", "Salvar alterações": True})
        self.assertTrue(contem(saida, "Já existe"))

    def test_normalizacao(self):
        self.assertEqual(dc.normalizar("  Programação   Web! "), dc.normalizar("programacao web"))
        self.assertEqual(dc.normalizar_codigo(" web 101 "), "WEB101")
        self.assertEqual(dc.id_por_codigo("web101"), dc.id_por_codigo(" WEB 101"))

    def test_documentos_antigos_sem_campo_ativa_contam_como_ativos(self):
        fs.criar("disciplinas", {"nome": "Antiga", "codigo": "OLD1", "curso": "X"})
        self.assertIn("Antiga", dc.listar_ativas()["nome"].tolist())

    def test_codigo_duplicado_barrado_mesmo_em_corrida(self):
        dc.cadastrar("Nova", "NOV1", "X")
        with mock.patch.object(dc, "_duplicada", return_value=None):              # ignora a checagem em lista
            with self.assertRaises(ValueError):
                dc.cadastrar("Outro nome", "nov1", "X")                           # o ID determinístico barra


if __name__ == "__main__":
    unittest.main()
