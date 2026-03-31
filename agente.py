import os
from anthropic import Anthropic
import src.tools as tools

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def rodar_comando(pergunta_usuario):
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system="Você é um assistente que ajuda o Sandro a gerenciar o PC dele. Use ferramentas de sistema quando necessário.",
            messages=[{"role": "user", "content": pergunta_usuario}]
        )
        
        texto_da_ia = response.content[0].text
        
        if any(p in pergunta_usuario.lower() for p in ["lista", "arquivo", "pasta", "tem aqui", "dir"]):
            res = tools.execute_tool("BashTool", "dir")
            return f"{texto_da_ia}\n\n--- Ação no Sistema ---\n{res.message}"
        
        return texto_da_ia
    except Exception as e:
        return f"❌ Erro: {str(e)}"