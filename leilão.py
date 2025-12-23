
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

DB_PATH = "leilao.db"

# ---------- Banco de dados ----------
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabela():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def inserir_lance(username: str, amount: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO bids (username, amount, timestamp) VALUES (?, ?, ?)",
        (username, amount, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def pegar_maior_lance():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT username, amount, timestamp FROM bids ORDER BY amount DESC, timestamp ASC LIMIT 1"
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def pegar_historico():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, amount, timestamp FROM bids ORDER BY timestamp DESC")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return pd.DataFrame(columns=["id", "username", "amount", "timestamp"])
    return pd.DataFrame([dict(r) for r in rows])


# ---------- Interface Streamlit ----------
st.set_page_config(page_title="Leilão Streamlit", layout="centered")
criar_tabela()

st.title("Leilão: lojas CPB!")
st.write("Insira seu nome e o valor do lance. O sistema mostrará qual lance está na frente.")
st.write("lojascpb@gmail.com")
# ------------------ FORM LANCE ------------------
with st.container():
    with st.form(key="form_lance"):
        nome = st.text_input("Nome do usuário", max_chars=50)
        valor = st.number_input("Valor do lance (R$)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Dar lance")

    if submitted:
        if not nome.strip():
            st.error("Informe um nome válido antes de dar o lance.")
        else:
            atual = pegar_maior_lance()
            atual_val = atual["amount"] if atual else 0.0

            if valor <= atual_val:
                st.warning(
                    f"Lance rejeitado: existe um lance maior ou igual em R$ {atual_val:.2f}."
                )
            else:
                inserir_lance(nome.strip(), float(valor))
                st.success(f"Lance de R$ {valor:.2f} registrado para {nome}")


# ------------------ LANCE LÍDER ------------------
lider = pegar_maior_lance()
st.markdown("### Lance líder")

if lider:
    st.write(f"**{lider['username']}** — R$ {float(lider['amount']):.2f}")
    st.caption(f"Registrado em (UTC): {lider['timestamp']}")
else:
    st.info("Nenhum lance registrado ainda. Seja o primeiro!")

# ------------------ HISTÓRICO ------------------
st.markdown("---")
st.markdown("### Histórico de lances")

df = pegar_historico()

if df.empty:
    st.write("Nenhum registro de lances.")
else:
    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
    except:
        pass

    st.dataframe(df[["id", "username", "amount", "timestamp"]])

# ------------------ ADMIN ------------------
with st.container():
    with st.expander("Admin — ações rápidas"):

        st.write("Funções administrativas requerem senha.")

        # Campo de senha
        senha = st.text_input("Senha do admin:", type="password")

        # Botão limpar lances
        if st.button("Limpar todos os lances"):
            if senha == "1234":
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM bids")
                conn.commit()
                conn.close()
                st.success("Todos os lances foram removidos.")
            else:
                st.error("Senha incorreta. Ação não permitida.")

        # Resetar banco
        if st.button("Resetar banco (recriar tabela)"):
            if senha == "1234":
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("DROP TABLE IF EXISTS bids")
                conn.commit()
                conn.close()
                criar_tabela()
                st.success("Banco reiniciado.")
            else:
                st.error("Senha incorreta. Ação não permitida.")

st.markdown("---")
st.caption(f"Arquivo do banco: {DB_PATH}")