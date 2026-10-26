import base64
import json
import random

import streamlit as st

st.set_page_config(page_title="Amigo Secreto", page_icon="🎁")


# ---------- funções auxiliares ----------
def codificar(quem: str, tirou: str) -> str:
    dados = json.dumps([quem, tirou]).encode("utf-8")
    return base64.urlsafe_b64encode(dados).decode("ascii")


def decodificar(texto: str):
    dados = base64.urlsafe_b64decode(texto.encode("ascii"))
    quem, tirou = json.loads(dados.decode("utf-8"))
    return quem, tirou


def proibido(a: str, b: str, restricoes: list) -> bool:
    if a == b:
        return True
    return any({a, b} == set(r) for r in restricoes)


def sortear(nomes: list, restricoes: list):
    for _ in range(5000):
        embaralhado = nomes[:]
        random.shuffle(embaralhado)
        if all(not proibido(n, e, restricoes) for n, e in zip(nomes, embaralhado)):
            return dict(zip(nomes, embaralhado))
    return None


# ---------- modo "link individual" ----------
# Se a pessoa abriu um link como ?d=XXXX, mostra só o resultado dela.
param = st.query_params.get("d")
if param:
    try:
        quem, tirou = decodificar(param)
        st.title("🎁 Amigo Secreto")
        st.write(f"Olá, **{quem}**! Seu amigo secreto é:")
        if st.button("👀 Revelar"):
            st.header(f"🎉 {tirou}")
            st.caption("Guarde segredo! 🤫")
    except Exception:
        st.error("Link inválido.")
    st.stop()


# ---------- estado ----------
if "restricoes" not in st.session_state:
    st.session_state.restricoes = []
if "sorteio" not in st.session_state:
    st.session_state.sorteio = None
if "revelado" not in st.session_state:
    st.session_state.revelado = None

st.title("🎁 Amigo Secreto")

# ---------- configuração ----------
if st.session_state.sorteio is None:
    texto = st.text_area(
        "Participantes (um nome por linha)",
        height=200,
        placeholder="Ana\nBruno\nCarla\nDiego",
    )
    nomes = []
    for linha in texto.splitlines():
        n = linha.strip()
        if n and n.lower() not in [x.lower() for x in nomes]:
            nomes.append(n)

    st.caption(f"{len(nomes)} participante(s)")

    st.subheader("Restrições (opcional)")
    st.caption("Ex.: casais que não devem se tirar. Vale nos dois sentidos.")
    par = st.multiselect("Escolha 2 pessoas", nomes, max_selections=2)
    if st.button("Adicionar restrição", disabled=len(par) != 2):
        if set(par) not in [set(r) for r in st.session_state.restricoes]:
            st.session_state.restricoes.append(par)
        st.rerun()

    # remove restrições de nomes que não existem mais
    st.session_state.restricoes = [
        r for r in st.session_state.restricoes if all(x in nomes for x in r)
    ]
    for i, r in enumerate(st.session_state.restricoes):
        c1, c2 = st.columns([4, 1])
        c1.write(f"🚫 {r[0]} ↔ {r[1]}")
        if c2.button("remover", key=f"rem{i}"):
            st.session_state.restricoes.pop(i)
            st.rerun()

    if st.button("🎲 Sortear!", type="primary"):
        if len(nomes) < 3:
            st.error("Adicione pelo menos 3 participantes.")
        else:
            resultado = sortear(nomes, st.session_state.restricoes)
            if resultado is None:
                st.error("Não foi possível sortear com essas restrições. Remova alguma.")
            else:
                st.session_state.sorteio = resultado
                st.rerun()

# ---------- resultado ----------
else:
    sorteio = st.session_state.sorteio
    st.success("Sorteio feito! Escolha como revelar.")

    tab1, tab2 = st.tabs(["📱 Passar o celular", "🔗 Links individuais"])

    with tab1:
        st.caption("Cada pessoa escolhe o próprio nome, vê quem tirou e esconde a tela.")
        if st.session_state.revelado is None:
            quem = st.selectbox("Quem é você?", list(sorteio.keys()))
            if st.button("Ver meu amigo secreto"):
                st.session_state.revelado = quem
                st.rerun()
        else:
            quem = st.session_state.revelado
            st.write(f"Olá, **{quem}**! Seu amigo secreto é:")
            st.header(f"🎉 {sorteio[quem]}")
            if st.button("🙈 Esconder"):
                st.session_state.revelado = None
                st.rerun()

    with tab2:
        st.caption(
            "Cole o endereço do seu app (depois de publicar) e copie o link de cada pessoa. "
            "Cada link mostra só o resultado daquela pessoa."
        )
        base = st.text_input("Endereço do app", "https://seu-app.streamlit.app")
        base = base.rstrip("/")
        for n, t in sorteio.items():
            st.write(f"**{n}**")
            st.code(f"{base}/?d={codificar(n, t)}", language=None)

    st.divider()
    if st.button("← Novo sorteio"):
        st.session_state.sorteio = None
        st.session_state.revelado = None
        st.rerun()
