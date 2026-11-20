"""Executa as páginas reais (app.py e pages/*.py) com um Streamlit falso + Firestore falso."""
import runpy
import unittest
from datetime import date, time, timedelta

from tests.test_atila import Base, AMANHA, ag, auth, fs, sala, sc, st, RAIZ, reserva

ADMIN = {"id": "adm", "nome": "Admin", "email": "admin@atila.local", "perfil": "Administrador"}
PROF = {"id": "prof", "nome": "Ana", "email": "ana@atila.local", "perfil": "Professor"}


def rodar(arquivo, entradas=None, usuario=ADMIN):
    st.resetar(entradas)
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


class TestPaginas(Base):
    def test_sem_login_redireciona(self):
        for pg in ("app.py", "pages/1_Salas.py", "pages/2_Nova_Reserva.py", "pages/3_Agendamentos.py",
                   "pages/4_Usuarios.py", "pages/5_Disciplinas.py", "pages/6_Perfil.py"):
            d, _, _ = rodar(pg, usuario=None)
            self.assertEqual(d, "switch:pages/0_Login.py", pg)

    def test_dashboard_mostra_dados_reais_do_firestore(self):
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
        self.assertNotIn("Ana Souza", recentes.to_string())

    def test_dashboard_vazio(self):
        _, saida, _ = rodar("app.py")
        self.assertTrue(contem(saida, "Nenhuma sala cadastrada"))
        self.assertTrue(contem(saida, "Nenhum agendamento cadastrado"))

    def test_dashboard_com_firestore_fora_mostra_erro_e_para(self):
        from unittest import mock
        con = fs._conexao()
        with mock.patch.object(con.sessao, "request", side_effect=ConnectionError("x")):
            d, saida, _ = rodar("app.py")
        self.assertEqual(d, "stop/rerun")
        self.assertTrue(contem(saida, "Não foi possível acessar o Firestore"))
        self.assertFalse(contem(saida, "Salas=0"))

    def test_fluxo_completo_sala_reserva_aprovacao_dashboard(self):
        # 1) admin cadastra sala
        rodar("pages/1_Salas.py", {"Nome da sala": "Lab 7", "Capacidade": 35, "Cadastrar sala": True})
        self.assertEqual(sc.listar()["sala"].tolist(), ["Lab 7"])

        # 2) professor solicita reserva
        entradas = {"Disciplina": "Banco de Dados", "Quantidade de alunos": 30, "Data": date.today() + timedelta(days=1),
                    "Solicitar reserva": True}
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", entradas, usuario=PROF)
        self.assertTrue(contem(saida, "Reserva enviada para análise"), saida)
        self.assertEqual(ag.listar().iloc[0]["status"], "Pendente")

        # 3) mesma sala/horário -> conflito
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", entradas, usuario=PROF)
        self.assertTrue(contem(saida, "Conflito de horário"), saida)
        self.assertEqual(len(ag.listar()), 1)

        # 4) admin confirma
        rid = ag.listar().iloc[0]["id"]
        d, _, _ = rodar("pages/3_Agendamentos.py", {"Atualizar status": True, "Novo status": "Confirmada", "Reserva": rid})
        self.assertEqual(d, "stop/rerun")
        self.assertEqual(ag.listar().iloc[0]["status"], "Confirmada")

        # 5) dashboard reflete
        _, saida, tabelas = rodar("app.py")
        for esperado in ("Salas=1", "Reservas=1", "Confirmadas=1"):
            self.assertTrue(contem(saida, esperado), (esperado, saida))
        self.assertEqual(tabelas[0].iloc[0]["reservas ativas (hoje em diante)"], 1)

    def test_nova_reserva_sem_salas(self):
        d, saida, _ = rodar("pages/2_Nova_Reserva.py", usuario=PROF)
        self.assertEqual(d, "stop/rerun")
        self.assertTrue(contem(saida, "Cadastre salas antes"))

    def test_nova_reserva_validacoes(self):
        sc.cadastrar(sala("S1", cap=40))
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", {"Solicitar reserva": True, "Disciplina": "",
                            "Data": date.today() - timedelta(days=1), "Horário final": time(13, 0)}, usuario=PROF)
        self.assertTrue(contem(saida, "Informe a disciplina"))
        self.assertTrue(contem(saida, "horário final deve ser posterior"))
        self.assertTrue(contem(saida, "não pode estar no passado"))
        self.assertTrue(ag.listar().empty)

    def test_reserva_excepcional_exige_justificativa(self):
        sc.cadastrar(sala("Pequena", cap=10))
        base = {"Disciplina": "X", "Quantidade de alunos": 30, "Data": date.today() + timedelta(days=1), "Solicitar reserva": True}
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", base, usuario=PROF)
        self.assertTrue(contem(saida, "exige justificativa"))
        self.assertTrue(contem(saida, "Informe a justificativa"))
        self.assertTrue(ag.listar().empty)
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", {**base, "Justificativa para reserva excepcional": "Evento"}, usuario=PROF)
        self.assertTrue(contem(saida, "Reserva enviada"))

    def test_recomendacao_melhor_encaixe(self):
        sc.cadastrar(sala("Grande", cap=200)); sc.cadastrar(sala("Media", cap=40)); sc.cadastrar(sala("Pequena", cap=10))
        _, saida, _ = rodar("pages/2_Nova_Reserva.py", {"Quantidade de alunos": 30}, usuario=PROF)
        self.assertTrue(contem(saida, "**Media**"), saida)

    def test_agendamentos_admin_ve_todas_e_conflito_ao_reativar(self):
        a = ag.criar(reserva()); ag.alterar_status(a, "Cancelada"); ag.criar(reserva())
        d, saida, _ = rodar("pages/3_Agendamentos.py", {"Atualizar status": True, "Novo status": "Confirmada", "Reserva": a})
        self.assertTrue(contem(saida, "conflito de horário"), saida)

    def test_agendamentos_professor_nao_ve_aprovacao(self):
        ag.criar(reserva())
        _, saida, tabelas = rodar("pages/3_Agendamentos.py", usuario=PROF)
        self.assertFalse(contem(saida, "Aprovação de reservas"))
        self.assertEqual(len(tabelas[0]), 1)

    def test_salas_professor_nao_ve_formulario(self):
        _, saida, _ = rodar("pages/1_Salas.py", usuario=PROF)
        self.assertTrue(contem(saida, "Somente administradores"))

    def test_salas_excluir_bloqueada_com_reserva(self):
        sid = sc.cadastrar(sala("Sala 101")); ag.criar(reserva())
        _, saida, _ = rodar("pages/1_Salas.py", {"Excluir sala": True, "Sala para excluir": sid})
        self.assertTrue(contem(saida, "reserva(s) pendente(s)/confirmada(s)"), saida)
        self.assertEqual(len(sc.listar()), 1)

    def test_salas_duplicada(self):
        sc.cadastrar(sala("Sala 101"))
        _, saida, _ = rodar("pages/1_Salas.py", {"Nome da sala": "sala 101", "Cadastrar sala": True})
        self.assertTrue(contem(saida, "Já existe uma sala"))

    def test_usuarios_e_autodesativacao(self):
        auth.login("admin@atila.local", "admin123"); st.session_state.clear()
        adm = fs.obter("usuarios", __import__("controllers.usuario_controller", fromlist=["x"]).id_por_email("admin@atila.local"))
        eu = {**ADMIN, "id": adm["id"]}
        _, saida, tabelas = rodar("pages/4_Usuarios.py", {"Salvar situação": True, "Situação": "Não", "Usuário": adm["id"]}, usuario=eu)
        self.assertTrue(contem(saida, "não pode desativar o seu próprio"))
        self.assertNotIn("senha", tabelas[0].columns)

    def test_disciplinas(self):
        _, _, tabelas = rodar("pages/5_Disciplinas.py")
        self.assertEqual(len(tabelas[0]), 3)
        rodar("pages/5_Disciplinas.py", {"Nome da disciplina": "Redes", "Código": "RED1", "Cadastrar disciplina": True})
        _, _, tabelas = rodar("pages/5_Disciplinas.py")
        self.assertEqual(len(tabelas[0]), 4)

    def test_login_e_criar_conta(self):
        d, _, _ = rodar("pages/0_Login.py", {"login_email": "admin@atila.local", "login_senha": "admin123", "Entrar": True}, usuario=None)
        self.assertEqual(d, "switch:app.py")
        _, saida, _ = rodar("pages/0_Login.py", {"login_email": "admin@atila.local", "login_senha": "x", "Entrar": True}, usuario=None)
        self.assertTrue(contem(saida, "inválidos"))
        self.assertFalse(contem(saida, "admin123"))                      # dica de senha padrão removida
        _, saida, _ = rodar("pages/0_Login.py", {"cad_nome": "N", "cad_email": "n@x.com", "cad_senha": "abcdef",
                            "cad_senha2": "abcdef", "Criar conta": True}, usuario=None)
        self.assertTrue(contem(saida, "Conta criada"))

    def test_perfil_alterar_senha(self):
        auth.login("ana@atila.local", "ana123")
        uid = st.session_state["usuario"]["id"]; usuario = dict(st.session_state["usuario"])
        _, saida, _ = rodar("pages/6_Perfil.py", {"pw_atual": "ana123", "pw_nova": "outra123", "pw_nova2": "outra123", "Alterar senha": True}, usuario=usuario)
        self.assertTrue(contem(saida, "Senha alterada"), saida)
        st.session_state.clear()
        self.assertTrue(auth.login("ana@atila.local", "outra123"))


if __name__ == "__main__":
    unittest.main()
