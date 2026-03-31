import streamlit as st
from agente import rodar_comando, limpar_historico, resumo_sessao

st.set_page_config(page_title="MeuClaude", page_icon="🤖", layout="centered")

st.title("🤖 MeuClaude")
st.caption("Assistente pessoal powered by Claude")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Digite sua mensagem..."):
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            resposta = rodar_comando(prompt)
        st.markdown(resposta)

    st.session_state.mensagens.append({"role": "assistant", "content": resposta})

with st.sidebar:
    st.header("⚙️ Sessão")
    st.write(resumo_sessao())
    if st.button("🧹 Limpar histórico"):
        limpar_historico()
        st.session_state.mensagens = []
        st.rerun()
