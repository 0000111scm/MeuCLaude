import os
import streamlit as st
from anthropic import Anthropic

st.set_page_config(page_title="MeuClaude", page_icon="🤖", layout="centered")

st.markdown("""
<style>
[data-testid="stChatMessage"] { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

api_key = os.environ.get("ANTHROPIC_API_KEY", "")
client = Anthropic(api_key=api_key) if api_key else None

SYSTEM = "Você é MeuClaude, assistente pessoal do 0000111scm. Ajuda com código, programação, arquivos, explicações técnicas, ideias, análises e qualquer tarefa. Responda sempre em português. Seja direto, prático e útil."

st.title("🤖 MeuClaude")
st.caption("Assistente pessoal · by 0000111")

if "msgs" not in st.session_state:
    st.session_state.msgs = []

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Manda sua pergunta..."):
    st.session_state.msgs.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            r = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=2048,
                system=SYSTEM,
                messages=st.session_state.msgs
            )
            reply = r.content[0].text
        st.markdown(reply)
    st.session_state.msgs.append({"role": "assistant", "content": reply})

with st.sidebar:
    st.header("⚙️ Sessão")
    st.write(f"💬 {len(st.session_state.msgs)//2} turnos")
    if st.button("🧹 Limpar"):
        st.session_state.msgs = []
        st.rerun()
