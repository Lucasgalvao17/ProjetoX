"""Testes de integração contra um Firestore falso local.  Rodar:  python -m unittest discover -s tests -v"""
import os
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent / "_stubs"))   # streamlit falso
sys.path.insert(0, str(RAIZ))

from tests import fake_firestore as ff   # noqa: E402

SRV, HOST = ff.iniciar()
os.environ["FIRESTORE_EMULATOR_HOST"] = HOST

import streamlit as st   # noqa: E402  (o falso)
st.secrets.update({"firestore": {"project_id": ff.PROJETO}})

from controllers import (agendamento_controller as ag, dashboard_controller as dash,   # noqa: E402
                         disciplina_controller as dc, sala_controller as sc, usuario_controller as uc)
from utils import auth, firestore_client as fs, tempo   # noqa: E402

AMANHA = str(tempo.hoje() + timedelta(days=1))


def sala(nome, cap=40, tipo="Teórica", **extra):
    return {"sala": nome, "capacidade": cap, "tipo": tipo, "campus": "C", "predio": "A", "andar": 1,
            "numero": "1", "computadores": 0, "projetor": "Sim", "ar_condicionado": "Sim",
            "acessibilidade": "Sim", "observacoes": "", **extra}


def reserva(salanome="Sala 101", ini="14:00", fim="16:00", data=AMANHA, prof="Prof X", status="Pendente"):
    return {"professor": prof, "disciplina": "Web", "sala": salanome, "tipo_aula": "Teórica", "alunos": 30,
            "data": data, "inicio": ini, "fim": fim, "status": status, "justificativa": "", "criado_por": "x@y.z"}


class Base(unittest.TestCase):
    def setUp(self):
        ff.ARMAZEM.colecoes.clear()
        ff.ARMAZEM.log.clear()
        st.session_state.clear()


class TestClienteFirestore(Base):
    def test_paginacao_le_todos_os_documentos(self):
        for i in range(650):
            fs.criar("salas", {"sala": f"S{i:03d}"})
        self.assertEqual(len(fs.listar("salas")), 650)   # a API devolve só 20 por padrão!

    def test_limite(self):
        for i in range(5):
            fs.criar("salas", {"sala": f"S{i}"})
        self.assertEqual(len(fs.listar("salas", limite=1)), 1)

    def test_conversao_de_tipos(self):
        import numpy as np
        d = fs.criar("x", {"a": np.int64(5), "b": 2.5, "c": True, "d": None, "e": "txt", "f": np.bool_(False)})
        lido = fs.obter("x", d["id"])
        self.assertEqual((lido["a"], lido["b"], lido["c"], lido["d"], lido["e"], lido["f"]),
                         (5, 2.5, True, "", "txt", False))
        self.assertIsInstance(lido["a"], int)

    def test_id_e_sempre_o_do_documento(self):
        fs.criar("salas", {"id": 7, "sala": "Antiga"})
        self.assertTrue(fs.listar("salas")[0]["id"].startswith("auto"))

    def test_atualizar_nao_cria_documento(self):
        with self.assertRaises(fs.DocumentoNaoEncontrado):
            fs.atualizar("salas", "inexistente", {"sala": "x"})
        self.assertEqual(fs.listar("salas"), [])

    def test_atualizar_so_muda_os_campos_informados(self):
        d = fs.criar("salas", {"sala": "A", "tipo": "T"})
        fs.atualizar("salas", d["id"], {"tipo": "Lab"})
        self.assertEqual(fs.obter("salas", d["id"])["sala"], "A")
        self.assertEqual(fs.obter("salas", d["id"])["tipo"], "Lab")

    def test_timestamp_normalizado_ordena_cronologicamente(self):
        a = fs.normalizar_timestamp("2026-11-20T12:00:00.00001Z")
        b = fs.normalizar_timestamp("2026-11-20T12:00:00.000011Z")
        c = fs.normalizar_timestamp("2026-11-20T12:00:00Z")
        self.assertTrue(c < a < b)

    def test_id_duplicado(self):
        fs.criar("u", {"a": 1}, doc_id="k")
        with self.assertRaises(fs.DocumentoJaExiste):
            fs.criar("u", {"a": 2}, doc_id="k")

    def test_erro_de_rede_vira_firestore_error(self):
        con = fs._conexao()
        with mock.patch.object(con.sessao, "request", side_effect=ConnectionError("boom")):
            with self.assertRaises(fs.FirestoreError):
                fs.listar("salas")


class TestSalas(Base):
    def test_cadastrar_listar_excluir(self):
        sid = sc.cadastrar(sala("Sala 101"))
        df = sc.listar()
        self.assertEqual(df["id"].tolist(), [sid])
        sc.excluir(sid)
        self.assertTrue(sc.listar().empty)

    def test_nome_duplicado_e_vazio(self):
        sc.cadastrar(sala("Sala 101"))
        with self.assertRaises(ValueError):
            sc.cadastrar(sala("  sala 101 "))
        with self.assertRaises(ValueError):
            sc.cadastrar(sala("   "))

    def test_nao_exclui_sala_com_reserva_ativa(self):
        sid = sc.cadastrar(sala("Sala 101"))
        rid = ag.criar(reserva())
        with self.assertRaises(ValueError):
            sc.excluir(sid)
        ag.alterar_status(rid, "Cancelada")
        sc.excluir(sid)

    def test_lista_vazia_tem_colunas(self):
        self.assertEqual(list(sc.listar().columns), sc.COLS)


class TestAgendamentos(Base):
    def test_conflito_na_criacao(self):
        ag.criar(reserva(ini="14:00", fim="16:00"))
        with self.assertRaises(ag.ConflitoHorario):
            ag.criar(reserva(ini="15:00", fim="17:00"))
        with self.assertRaises(ag.ConflitoHorario):
            ag.criar(reserva(ini="13:00", fim="14:30"))
        with self.assertRaises(ag.ConflitoHorario):
            ag.criar(reserva(ini="14:30", fim="15:00"))     # contida
        self.assertEqual(len(ag.listar()), 1)

    def test_horarios_adjacentes_nao_conflitam(self):
        ag.criar(reserva(ini="14:00", fim="16:00"))
        ag.criar(reserva(ini="16:00", fim="18:00"))
        ag.criar(reserva(ini="12:00", fim="14:00"))
        ag.criar(reserva(salanome="Outra", ini="14:00", fim="16:00"))
        ag.criar(reserva(data=str(tempo.hoje() + timedelta(days=2))))
        self.assertEqual(len(ag.listar()), 5)

    def test_cancelada_e_reprovada_liberam_o_horario(self):
        rid = ag.criar(reserva())
        ag.alterar_status(rid, "Reprovada")
        ag.criar(reserva())

    def test_fluxo_aprovacao(self):
        rid = ag.criar(reserva())
        self.assertEqual(ag.listar().iloc[0]["status"], "Pendente")
        ag.alterar_status(rid, "Confirmada", "admin@x")
        linha = ag.listar().iloc[0]
        self.assertEqual((linha["status"], linha["atualizado_por"]), ("Confirmada", "admin@x"))
        self.assertTrue(linha["atualizado_em"])

    def test_reativar_revalida_conflito(self):
        a = ag.criar(reserva())
        ag.alterar_status(a, "Cancelada")
        ag.criar(reserva())                                  # outro ocupa o horário
        with self.assertRaises(ag.ConflitoHorario):
            ag.alterar_status(a, "Confirmada")               # não pode ressuscitar a antiga

    def test_validacoes(self):
        with self.assertRaises(ValueError):
            ag.criar(reserva(ini="16:00", fim="14:00"))
        with self.assertRaises(ValueError):
            ag.criar({**reserva(), "disciplina": ""})
        with self.assertRaises(ValueError):
            ag.alterar_status("x", "Qualquer")
        with self.assertRaises(ValueError):
            ag.alterar_status("inexistente", "Confirmada")

    def test_corrida_o_mais_recente_desfaz_a_propria_reserva(self):
        """Simula duas pessoas reservando juntas: a 2ª não enxerga a 1ª no pré-check."""
        primeira = fs.criar("reservas", reserva(prof="Primeira"))
        real = ag.listar
        chamadas = {"n": 0}

        def listar_defasado():
            chamadas["n"] += 1
            return real().iloc[0:0] if chamadas["n"] == 1 else real()

        with mock.patch.object(ag, "listar", listar_defasado):
            with self.assertRaises(ag.ConflitoHorario):
                ag.criar(reserva(prof="Segunda"))
        restantes = ag.listar()
        self.assertEqual(restantes["professor"].tolist(), ["Primeira"])
        self.assertEqual(restantes["id"].tolist(), [primeira["id"]])

    def test_corrida_o_mais_antigo_permanece(self):
        """Se o rival chegou DEPOIS, a minha reserva fica (o rival é quem desfaz)."""
        real = ag.listar
        n = {"i": 0}

        def listar_com_rival_tardio():
            n["i"] += 1
            if n["i"] == 2:                                   # entre o pré-check e o re-check
                fs.criar("reservas", reserva(prof="Rival tardio"))
            return real()

        with mock.patch.object(ag, "listar", listar_com_rival_tardio):
            novo_id = ag.criar(reserva(prof="Minha"))
        self.assertIn(novo_id, ag.listar()["id"].tolist())

    def test_ordem_com_fracoes_de_tamanhos_diferentes(self):
        antes = {"criado_em": "2026-11-20T12:00:00.5Z", "id": "b"}
        depois = {"criado_em": "2026-11-20T12:00:00.5123Z", "id": "a"}
        self.assertLess(ag._chave_ordem(antes), ag._chave_ordem(depois))   # string pura erraria


class TestDashboardUnificado(Base):
    def test_dashboard_reflete_exatamente_o_firestore(self):
        """O bug original: Dashboard lia CSV e divergia das abas."""
        d = dash.obter_dados()
        self.assertEqual(d["metricas"]["Salas"], 0)
        self.assertEqual(d["metricas"]["Reservas"], 0)
        self.assertNotIn("Ana Souza", d["recentes"].to_string())      # mock antigo sumiu

        s1 = sc.cadastrar(sala("Sala Real A", cap=50))
        sc.cadastrar(sala("Sala Real B", cap=20))
        r1 = ag.criar(reserva("Sala Real A", prof="Maria"))
        r2 = ag.criar(reserva("Sala Real A", ini="17:00", fim="18:00", prof="João"))
        ag.alterar_status(r1, "Confirmada")

        d = dash.obter_dados()
        self.assertEqual(d["metricas"]["Salas"], 2)
        self.assertEqual(d["metricas"]["Reservas"], 2)
        self.assertEqual(d["metricas"]["Confirmadas"], 1)
        self.assertEqual(d["metricas"]["Pendentes"], 1)
        # mesma fonte das abas
        self.assertEqual(d["salas"]["id"].tolist(), sc.listar()["id"].tolist())
        self.assertEqual(sorted(d["reservas"]["id"]), sorted(ag.listar()["id"]))
        self.assertEqual(set(d["visao_salas"]["sala"]), {"Sala Real A", "Sala Real B"})
        ativas = dict(zip(d["visao_salas"]["sala"], d["visao_salas"]["reservas_ativas"]))
        self.assertEqual(ativas, {"Sala Real A": 2, "Sala Real B": 0})
        self.assertIn(s1, d["visao_salas"]["id"].tolist())

    def test_novas_salas_e_exclusoes_aparecem_na_hora(self):
        sid = sc.cadastrar(sala("Nova"))
        self.assertEqual(dash.obter_dados()["metricas"]["Salas"], 1)
        sc.excluir(sid)
        self.assertEqual(dash.obter_dados()["metricas"]["Salas"], 0)

    def test_recentes_ordenadas_pela_criacao_e_limitadas_a_10(self):
        for i in range(12):
            ag.criar(reserva(ini=f"{6+i:02d}:00", fim=f"{6+i:02d}:30", prof=f"P{i}"))
        rec = dash.obter_dados()["recentes"]
        self.assertEqual(len(rec), 10)
        self.assertEqual(rec.iloc[0]["professor"], "P11")

    def test_mais_de_20_reservas_nao_sao_truncadas(self):
        for i in range(45):
            fs.criar("reservas", reserva(prof=f"P{i}", ini=f"{i%24:02d}:00", fim=f"{i%24:02d}:30"))
        self.assertEqual(dash.obter_dados()["metricas"]["Reservas"], 45)

    def test_reserva_para_sala_inexistente_e_sinalizada(self):
        fs.criar("reservas", reserva("Sala Fantasma"))
        self.assertEqual(len(dash.obter_dados()["reservas_orfas"]), 1)

    def test_usuarios_contados_do_firestore(self):
        d = dash.obter_dados()                                   # semeia admin + ana (1ª vez)
        self.assertEqual(d["metricas"]["Usuários"], 2)
        auth.cadastrar_usuario("Novo", "novo@x.com", "123456", "Professor")
        self.assertEqual(dash.obter_dados()["metricas"]["Usuários"], 3)

    def test_falha_do_firestore_nao_vira_zero_silencioso(self):
        con = fs._conexao()
        with mock.patch.object(con.sessao, "request", side_effect=ConnectionError("x")):
            with self.assertRaises(fs.FirestoreError):
                dash.obter_dados()


class TestAuth(Base):
    def test_admin_inicial_importado_do_seed_e_senha_migrada(self):
        self.assertTrue(auth.login("admin@atila.local", "admin123"))
        self.assertEqual(st.session_state["usuario"]["perfil"], "Administrador")
        guardado = fs.obter("usuarios", uc.id_por_email("admin@atila.local"))["senha"]
        self.assertTrue(guardado.startswith("pbkdf2_sha256$"))      # SHA-256 puro foi trocado
        st.session_state.clear()
        self.assertTrue(auth.login("ADMIN@atila.local ", "admin123"))   # continua entrando

    def test_senha_errada_e_usuario_inexistente(self):
        self.assertFalse(auth.login("admin@atila.local", "errada"))
        self.assertFalse(auth.login("naoexiste@x.com", "123456"))
        self.assertFalse(auth.login("", ""))
        self.assertNotIn("usuario", st.session_state)

    def test_usuario_inativo_nao_entra(self):
        auth.login("ana@atila.local", "ana123"); st.session_state.clear()
        uc.definir_ativo(uc.id_por_email("ana@atila.local"), "Não")
        self.assertFalse(auth.login("ana@atila.local", "ana123"))

    def test_cadastro_e_email_duplicado(self):
        ok, _ = auth.cadastrar_usuario("Zé", "ze@x.com", "segredo1", "Professor")
        self.assertTrue(ok)
        ok, msg = auth.cadastrar_usuario("Zé2", "ZE@x.com", "segredo1", "Professor")
        self.assertFalse(ok); self.assertIn("já está cadastrado", msg)
        self.assertTrue(auth.login("ze@x.com", "segredo1"))

    def test_validacoes_de_cadastro(self):
        self.assertFalse(auth.cadastrar_usuario("", "a@b.co", "123456")[0])
        self.assertFalse(auth.cadastrar_usuario("A", "invalido", "123456")[0])
        self.assertFalse(auth.cadastrar_usuario("A", "a@b.co", "123")[0])
        self.assertFalse(auth.cadastrar_usuario("A", "a@b.co", "123456", "Hacker")[0])

    def test_alterar_senha(self):
        auth.login("admin@atila.local", "admin123")
        uid = st.session_state["usuario"]["id"]
        self.assertFalse(auth.alterar_senha(uid, "errada", "novasenha")[0])
        self.assertFalse(auth.alterar_senha(uid, "admin123", "123")[0])
        self.assertTrue(auth.alterar_senha(uid, "admin123", "novasenha")[0])
        st.session_state.clear()
        self.assertFalse(auth.login("admin@atila.local", "admin123"))
        self.assertTrue(auth.login("admin@atila.local", "novasenha"))

    def test_hash_com_sal(self):
        self.assertNotEqual(uc.gerar_hash("abc123"), uc.gerar_hash("abc123"))
        self.assertTrue(uc.verificar_senha("abc123", uc.gerar_hash("abc123")))
        self.assertFalse(uc.verificar_senha("abc124", uc.gerar_hash("abc123")))
        self.assertFalse(uc.verificar_senha("x", "pbkdf2_sha256$lixo"))

    def test_seed_nao_duplica_nem_sobrescreve(self):
        uc.listar(); uc.listar(); uc.obter_por_email("admin@atila.local")
        self.assertEqual(len(fs.listar("usuarios")), 2)

    def test_lista_de_usuarios_nao_expoe_senha(self):
        self.assertNotIn("senha", uc.listar().columns)


try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    TEM_CRYPTO = True
except ImportError:      # pragma: no cover
    TEM_CRYPTO = False


@unittest.skipUnless(TEM_CRYPTO, "cryptography não instalado")
class TestChaveDaContaDeServico(unittest.TestCase):
    """Chave RSA DESCARTÁVEL gerada na hora; simula colagens defeituosas nos Secrets."""

    @classmethod
    def setUpClass(cls):
        k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.pem = k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                  serialization.NoEncryption()).decode()
        cls.base = {"type": "service_account", "project_id": "p", "private_key_id": "abc",
                    "client_email": "sa@p.iam.gserviceaccount.com", "token_uri": "https://oauth2.googleapis.com/token"}

    def _carrega(self, texto):
        chave = fs.normalizar_chave_privada(texto)
        serialization.load_pem_private_key(chave.encode(), password=None)     # levanta ValueError se inválida
        return chave

    def test_variantes_de_colagem_viram_pem_valido(self):
        corpo = self.pem
        variantes = {
            "correta": corpo,
            "barra-n literal": corpo.replace("\n", "\\n"),
            "barra-n duplo": corpo.replace("\n", "\\\\n"),
            "espacos no lugar de quebras": corpo.replace("\n", " "),
            "crlf": corpo.replace("\n", "\r\n"),
            "entre aspas": '"' + corpo.replace("\n", "\\n") + '"',
            "sem quebra final": corpo.rstrip("\n"),
            "quebras literais com cr": corpo.replace("\n", "\\r\\n"),
        }
        for nome, texto in variantes.items():
            with self.subTest(nome):
                self.assertEqual(self._carrega(texto), self.pem)

    def test_conta_valida_sem_problemas(self):
        self.assertEqual(fs.problemas_conta({**self.base, "private_key": self.pem}), [])

    def test_campos_ausentes_sao_nomeados(self):
        info = {k: v for k, v in self.base.items() if k not in ("token_uri", "private_key_id")}
        achados = " ".join(fs.problemas_conta({**info, "private_key": self.pem}))
        self.assertIn("token_uri", achados)
        self.assertIn("private_key_id", achados)

    def test_chave_truncada_e_sem_cabecalho(self):
        cortada = self.pem[:len(self.pem) // 2]
        self.assertTrue(any("BEGIN/END" in a for a in fs.problemas_conta({**self.base, "private_key": cortada})))
        meio = fs.normalizar_chave_privada(self.pem[: len(self.pem) // 2] + "\n-----END PRIVATE KEY-----")
        self.assertTrue(any("truncada" in a for a in fs.problemas_conta({**self.base, "private_key": meio})))

    def test_mensagem_de_diagnostico_nao_vaza_a_chave(self):
        achados = " ".join(fs.problemas_conta({**self.base, "private_key": self.pem[:300]}))
        corpo = self.pem.splitlines()[1]
        self.assertNotIn(corpo, achados)


class TestDisciplinas(Base):
    def test_seed_e_cadastro(self):
        self.assertEqual(len(dc.listar()), 3)
        dc.cadastrar("Redes", "RED401", "SI")
        self.assertEqual(len(dc.listar()), 4)
        with self.assertRaises(ValueError):
            dc.cadastrar("Outra", "red401", "SI")
        with self.assertRaises(ValueError):
            dc.cadastrar("", "X", "SI")

    def test_seed_so_roda_com_colecao_vazia(self):
        dc.cadastrar("Redes", "RED401", "SI")   # lista antes via listar() -> semeia
        n = len(dc.listar()); dc.listar()
        self.assertEqual(len(dc.listar()), n)


class TestExcluirDisciplina(Base):
    ONTEM = str(tempo.hoje() - timedelta(days=1))

    def _id(self, codigo):
        return dc.listar().set_index("codigo").loc[codigo, "id"]

    def test_exclui_e_devolve_o_nome(self):
        did = self._id("BD201")
        self.assertEqual(dc.excluir(did), "Banco de Dados")
        self.assertIsNone(fs.obter("disciplinas", did))
        self.assertNotIn("BD201", dc.listar()["codigo"].tolist())

    def test_inexistente(self):
        dc.listar()
        with self.assertRaises(ValueError):
            dc.excluir("nao-existe")

    def test_bloqueia_com_reserva_pendente_ou_confirmada_por_vir(self):
        did = self._id("WEB101")
        rid = ag.criar({**reserva(), "disciplina_id": did})
        with self.assertRaises(ValueError) as e:
            dc.excluir(did)
        self.assertIn("1 reserva(s)", str(e.exception))
        ag.alterar_status(rid, "Confirmada")
        with self.assertRaises(ValueError):
            dc.excluir(did)
        self.assertIsNotNone(fs.obter("disciplinas", did))

    def test_libera_quando_a_reserva_foi_cancelada_ou_reprovada_ou_ja_passou(self):
        did = self._id("WEB101")
        a = ag.criar({**reserva(), "disciplina_id": did}); ag.alterar_status(a, "Cancelada")
        b = ag.criar({**reserva(ini="08:00", fim="09:00"), "disciplina_id": did}); ag.alterar_status(b, "Reprovada")
        c = ag.criar({**reserva(data=self.ONTEM), "disciplina_id": did}); ag.alterar_status(c, "Confirmada")
        d = ag.criar({**reserva(ini="10:00", fim="11:00", data=self.ONTEM), "disciplina_id": did})   # pendente vencida
        dc.excluir(did)
        self.assertIsNone(fs.obter("disciplinas", did))
        self.assertEqual(len(ag.listar()), 4)                                     # o histórico não é tocado
        self.assertTrue((ag.listar()["disciplina_id"] == did).all())

    def test_reserva_antiga_sem_disciplina_id_casa_pelo_nome(self):
        dc.listar()
        fs.criar("reservas", {**reserva(), "disciplina": "Banco  de DADOS"})      # sem disciplina_id
        with self.assertRaises(ValueError):
            dc.excluir(self._id("BD201"))
        dc.excluir(self._id("ES301"))                                             # outra disciplina não é afetada

    def test_reserva_de_outra_disciplina_nao_bloqueia(self):
        ag.criar({**reserva(), "disciplina_id": self._id("WEB101")})
        dc.excluir(self._id("BD201"))

    def test_excluir_todas_nao_faz_o_seed_repovoar(self):
        for _, r in dc.listar().iterrows():
            dc.excluir(r["id"])
        self.assertEqual(len(dc.listar()), 0)
        self.assertEqual(len(dc.listar()), 0)                                     # e continua vazia nas leituras seguintes

    def test_excluir_uma_base_antiga_sem_marcador_tambem_nao_repovoa(self):
        fs.criar("disciplinas", {"nome": "Única", "codigo": "UNI1", "curso": "X", "ativa": "Sim"}, doc_id=dc.id_por_codigo("UNI1"))
        dc.excluir(dc.id_por_codigo("UNI1"))                                      # base já existia, sem marcador de seed
        self.assertEqual(len(dc.listar()), 0)

    def test_pode_recadastrar_o_mesmo_codigo_depois_de_excluir(self):
        did = self._id("BD201")
        dc.excluir(did)
        self.assertEqual(dc.cadastrar("Banco de Dados", "BD201", "SI"), did)

    def test_nova_reserva_com_disciplina_excluida_e_recusada(self):
        did = self._id("BD201")
        dc.excluir(did)
        with self.assertRaises(ValueError):
            ag.criar({**reserva(), "disciplina_id": did})


if __name__ == "__main__":
    unittest.main()
