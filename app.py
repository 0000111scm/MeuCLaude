import os
import streamlit as st
from groq import Groq

st.set_page_config(page_title="MeuClaude", page_icon="🤖", layout="centered")

client = Groq(api_key="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")

SYSTEM = "Você é MeuClaude, assistente pessoal do 0000111scm. Especialista em código e programação. Responda sempre em português. Seja direto, prático e útil."

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
            r = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": SYSTEM}] + st.session_state.msgs,
                max_tokens=2048
            )
            reply = r.choices[0].message.content
        st.markdown(reply)
    st.session_state.msgs.append({"role": "assistant", "content": reply})

with st.sidebar:
    st.header("⚙️ Sessão")
    st.write(f"💬 {len(st.session_state.msgs)//2} turnos")
    if st.button("🧹 Limpar"):
        st.session_state.msgs = []
        st.rerun()
