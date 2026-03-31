import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

historico = []

SYSTEM_PROMPT = """Você é MeuClaude, assistente pessoal do 0000111.
Você ajuda com tarefas de programação, gerenciamento de arquivos, explicações técnicas e muito mais.
Responda sempre em português. Seja direto e prático."""

def rodar_comando(pergunta_usuario: str) -> str:
    try:
        historico.append({"role": "user", "content": pergunta_usuario})

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=historico
        )

        resposta = response.content[0].text
        historico.append({"role": "assistant", "content": resposta})

        return resposta
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def limpar_historico():
    historico.clear()
    return "🧹 Histórico limpo!"

def resumo_sessao() -> str:
    return f"💬 {len(historico) // 2} turnos na sessão atual."
