import streamlit as st
from src.tools import execute_tool
from src.runtime import PortRuntime

st.set_page_config(page_title="Claude OS Console", page_icon="💻", layout="wide")

if "historico" not in st.session_state:
    st.session_state.historico = []
if "turnos" not in st.session_state:
    st.session_state.turnos = []

st.title("🎮 Claude Python — Console de Controle")
st.caption("Portabilidade das ferramentas do Claude Code para Python · Windows CMD")
st.divider()

aba1, aba2 = st.tabs(["🔧 Console de Ferramentas", "🧠 Turn Loop (Runtime)"])

# ════════════════════════════════════════════════════════════
# ABA 1 — Console de Ferramentas (igual ao anterior)
# ════════════════════════════════════════════════════════════
with aba1:
    col_esq, col_dir = st.columns([1, 2])

    SUGESTOES = {
        "BashTool":     ["dir", "ipconfig", "whoami", "systeminfo", "tasklist"],
        "FileReadTool": ["README.md", "src/tools.py", "app.py", "requirements.txt"],
        "FileWriteTool":["output.txt: Conteúdo aqui", "notes.txt: Anotações do teste"],
        "GlobTool":     ["src/*.py", "**/*.json", "**/*.txt", "*.md"],
        "GrepTool":     ["def >> src/tools.py", "import >> src/tools.py", "erro >> ."],
        "FileEditTool": ["app.py || old: texto antigo || new: texto novo"],
    }

    AJUDA = {
        "BashTool":     "Executa comandos CMD do Windows",
        "FileReadTool": "Lê o conteúdo completo de um arquivo",
        "FileWriteTool":"Cria ou sobrescreve um arquivo",
        "GlobTool":     "Busca arquivos por padrão: src/*.py  ou  **/*.json base_dir=C:/pasta",
        "GrepTool":     "Busca texto em arquivo/pasta: padrão >> caminho",
        "FileEditTool": "Edita trecho exato: arquivo.py || old: texto velho || new: texto novo",
    }

    with col_esq:
        st.subheader("⚙️ Configuração")
        ferramenta = st.selectbox("Ferramenta:", list(SUGESTOES.keys()))
        st.caption(f"ℹ️ {AJUDA[ferramenta]}")

        sugestao = st.selectbox(
            "💡 Sugestões rápidas:",
            ["— escolha ou digite abaixo —"] + SUGESTOES[ferramenta]
        )
        comando = st.text_input(
            "Comando / Payload:",
            value="" if sugestao.startswith("—") else sugestao,
            placeholder=SUGESTOES[ferramenta][0]
        )
        timeout = 30
        if ferramenta == "BashTool":
            timeout = st.slider("⏱️ Timeout (segundos):", 5, 120, 30)

        executar = st.button("🚀 Executar", use_container_width=True, type="primary", key="btn_aba1")

    with col_dir:
        st.subheader("📟 Saída do Sistema")
        if executar:
            if not comando.strip():
                st.warning("⚠️ Escreva um comando ou payload antes de executar.")
            else:
                payload = f"{comando} || timeout={timeout}" if ferramenta == "BashTool" else comando
                with st.spinner(f"Executando `{ferramenta}`..."):
                    resultado = execute_tool(ferramenta, payload)

                st.session_state.historico.append({
                    "ferramenta": ferramenta,
                    "comando": comando,
                    "mensagem": resultado.message,
                    "handled": resultado.handled,
                })

                msg = resultado.message
                if not resultado.handled:               st.error(msg)
                elif msg.startswith("✅"):              st.success(msg)
                elif msg.startswith(("⚠️","⏱️","🚫")): st.warning(msg)
                elif msg.startswith("❌"):              st.error(msg)
                else:                                   st.info(msg)

                st.markdown("**Saída bruta (copiável):**")
                st.code(msg, language="bash")
        else:
            st.info("Configure a ferramenta à esquerda e clique em **🚀 Executar**.")

    if st.session_state.historico:
        st.divider()
        st.subheader("🕓 Histórico da Sessão")
        for i, item in enumerate(reversed(st.session_state.historico)):
            numero = len(st.session_state.historico) - i
            icone  = "✅" if item["handled"] else "❌"
            with st.expander(f"{icone} #{numero} · {item['ferramenta']} · `{item['comando']}`"):
                st.code(item["mensagem"], language="bash")
        if st.button("🗑️ Limpar histórico", key="limpar_aba1"):
            st.session_state.historico = []
            st.rerun()

# ════════════════════════════════════════════════════════════
# ABA 2 — Turn Loop (PortRuntime)
# ════════════════════════════════════════════════════════════
with aba2:
    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.subheader("🧠 Configuração do Runtime")
        st.caption("O prompt é roteado pelo PortRuntime e processado em múltiplos turnos.")

        prompt = st.text_area(
            "Prompt livre:",
            placeholder="ex: leia o arquivo src/tools.py e me diga quantas funções ele tem",
            height=150
        )
        max_turns = st.slider("🔄 Máximo de turnos:", 1, 10, 3)
        limit     = st.slider("🎯 Limite de matches:", 1, 20, 5)
        structured = st.checkbox("📦 Saída estruturada (JSON)")

        rodar = st.button("▶️ Rodar Turn Loop", use_container_width=True, type="primary", key="btn_aba2")

    with col_b:
        st.subheader("📜 Resultado dos Turnos")

        if rodar:
            if not prompt.strip():
                st.warning("⚠️ Digite um prompt antes de rodar.")
            else:
                with st.spinner("PortRuntime processando turnos..."):
                    try:
                        runtime = PortRuntime()

                        # Mostra o roteamento antes dos turnos
                        matches = runtime.route_prompt(prompt, limit=limit)
                        if matches:
                            st.markdown("**🗺️ Roteamento do prompt:**")
                            route_lines = [f"- `{m.kind}` · **{m.name}** · score={m.score}" for m in matches]
                            st.markdown("\n".join(route_lines))
                            st.divider()

                        # Executa o turn loop
                        results = runtime.run_turn_loop(
                            prompt,
                            limit=limit,
                            max_turns=max_turns,
                            structured_output=structured
                        )

                        # Salva no histórico de turnos
                        st.session_state.turnos.append({
                            "prompt": prompt,
                            "results": [(r.output, r.stop_reason) for r in results]
                        })

                        # Exibe cada turno
                        for idx, result in enumerate(results, start=1):
                            cor = "✅" if result.stop_reason == "end_turn" else "🔄"
                            with st.expander(f"{cor} Turno {idx} — stop_reason: `{result.stop_reason}`", expanded=True):
                                st.code(result.output, language="markdown")

                    except Exception as e:
                        st.error(f"❌ ERRO NO RUNTIME: {str(e)}")
        else:
            st.info("Digite um prompt à esquerda e clique em **▶️ Rodar Turn Loop**.")

        # Histórico de prompts da sessão
        if st.session_state.turnos:
            st.divider()
            st.subheader("🕓 Prompts Anteriores")
            for i, sessao in enumerate(reversed(st.session_state.turnos)):
                with st.expander(f"💬 #{len(st.session_state.turnos)-i} · `{sessao['prompt'][:60]}...`"):
                    for idx, (output, stop) in enumerate(sessao["results"], 1):
                        st.markdown(f"**Turno {idx}** · `{stop}`")
                        st.code(output, language="markdown")
            if st.button("🗑️ Limpar histórico", key="limpar_aba2"):
                st.session_state.turnos = []
                st.rerun()