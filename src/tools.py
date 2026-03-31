from __future__ import annotations
import json
import os
import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from .models import PortingBacklog, PortingModule
from .permissions import ToolPermissionContext

SNAPSHOT_PATH = Path(__file__).resolve().parent / 'reference_data' / 'tools_snapshot.json'

@dataclass(frozen=True)
class ToolExecution:
    name: str
    source_hint: str
    payload: str
    handled: bool
    message: str

@lru_cache(maxsize=1)
def load_tool_snapshot() -> tuple[PortingModule, ...]:
    if not SNAPSHOT_PATH.exists():
        return tuple()
    raw_entries = json.loads(SNAPSHOT_PATH.read_text())
    return tuple(
        PortingModule(
            name=e['name'],
            responsibility=e['responsibility'],
            source_hint=e['source_hint'],
            status='mirrored'
        )
        for e in raw_entries
    )

PORTED_TOOLS = load_tool_snapshot()

def get_tool(name: str) -> PortingModule | None:
    needle = name.lower()
    for m in PORTED_TOOLS:
        if m.name.lower() == needle:
            return m
    return None

def _run_bash(command: str, timeout: int = 30) -> str:
    BLOCKED = ('rm -rf /', 'mkfs', ':(){ :|:& };:', 'dd if=/dev/zero', 'format c:')
    if any(b in command.lower() for b in BLOCKED):
        return "🚫 BLOQUEADO: Comando recusado por política de segurança."
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            timeout=timeout, cwd=os.getcwd(),
        )
        stdout = result.stdout.decode('cp850', errors='replace').strip()
        stderr = result.stderr.decode('cp850', errors='replace').strip()
        code   = result.returncode
        parts  = []
        if stdout: parts.append(f"STDOUT:\n{stdout}")
        if stderr: parts.append(f"STDERR:\n{stderr}")
        output = "\n\n".join(parts) if parts else "(sem saída)"
        prefix = "✅" if code == 0 else f"⚠️ (exit {code})"
        return f"{prefix} BASH:\n{output}"
    except subprocess.TimeoutExpired:
        return f"⏱️ TIMEOUT: Comando excedeu {timeout}s e foi encerrado."
    except FileNotFoundError:
        return "❌ ERRO: Shell não encontrado."
    except Exception as e:
        return f"❌ ERRO DE SISTEMA: {str(e)}"


def _run_glob(pattern: str, base_dir: str = '.') -> str:
    try:
        base    = Path(base_dir).resolve()
        matches = sorted(base.glob(pattern))
        if not matches:
            return f"🔍 GLOB: Nenhum arquivo encontrado para '{pattern}' em '{base}'"
        lines = [f"  {'📁' if p.is_dir() else '📄'} {p.relative_to(base)}" for p in matches]
        return f"🔍 GLOB: {len(matches)} resultado(s) para '{pattern}':\n" + "\n".join(lines)
    except Exception as e:
        return f"❌ ERRO GLOB: {str(e)}"


def _run_grep(pattern: str, target: str, context_lines: int = 2) -> str:
    try:
        path = Path(target)
        if not path.exists():
            return f"❌ ERRO GREP: '{target}' não encontrado."
        files = list(path.rglob('*')) if path.is_dir() else [path]
        files = [f for f in files if f.is_file()]
        results = []
        regex   = re.compile(pattern, re.IGNORECASE)
        for file in files:
            try:
                lines = file.read_text(encoding='utf-8', errors='replace').splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines):
                if regex.search(line):
                    start = max(0, i - context_lines)
                    end   = min(len(lines), i + context_lines + 1)
                    bloco = []
                    for j in range(start, end):
                        marcador = ">>>" if j == i else "   "
                        bloco.append(f"  {marcador} {j+1:4d} │ {lines[j]}")
                    results.append(f"\n📄 {file}\n" + "\n".join(bloco))
        if not results:
            return f"🔎 GREP: Nenhuma ocorrência de '{pattern}' em '{target}'"
        return f"🔎 GREP: {len(results)} ocorrência(s) de '{pattern}':\n" + "\n".join(results)
    except Exception as e:
        return f"❌ ERRO GREP: {str(e)}"


def _run_edit(filename: str, old_text: str, new_text: str) -> str:
    try:
        path = Path(filename)
        if not path.exists():
            return f"❌ ERRO EDIT: Arquivo '{filename}' não encontrado."
        content = path.read_text(encoding='utf-8')
        if old_text not in content:
            return f"❌ ERRO EDIT: Trecho não encontrado em '{filename}'.\nVerifique maiúsculas e espaços."
        count   = content.count(old_text)
        updated = content.replace(old_text, new_text, 1)
        path.write_text(updated, encoding='utf-8')
        aviso = f" (atenção: havia {count} ocorrências, apenas a 1ª foi substituída)" if count > 1 else ""
        return f"✅ EDIT: '{filename}' atualizado com sucesso{aviso}."
    except Exception as e:
        return f"❌ ERRO EDIT: {str(e)}"


def execute_tool(name: str, payload: str = '') -> ToolExecution:
    module = get_tool(name)
    if module is None:
        return ToolExecution(
            name=name, source_hint='', payload=payload,
            handled=False, message=f'Ferramenta desconhecida: {name}'
        )

    name_l  = name.lower()
    message = ""

    try:
        if "read" in name_l:
            file_match = re.search(r'([\w\./\\]+\.\w+)', payload)
            filename   = file_match.group(1) if file_match else payload.strip()
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                message = f"📖 CONTEÚDO DE '{filename}':\n\n{content}"
            else:
                message = f"❌ ERRO: Arquivo '{filename}' não encontrado."

        elif "bash" in name_l:
            timeout_match = re.search(r'\|\|\s*timeout=(\d+)', payload)
            timeout  = int(timeout_match.group(1)) if timeout_match else 30
            command  = re.sub(r'\|\|\s*timeout=\d+', '', payload).strip()
            message  = _run_bash(command, timeout=timeout)

        elif "glob" in name_l:
            dir_match = re.search(r'base_dir=(\S+)', payload)
            base_dir  = dir_match.group(1) if dir_match else '.'
            pattern   = re.sub(r'base_dir=\S+', '', payload).strip()
            message   = _run_glob(pattern, base_dir)

        elif "grep" in name_l:
            parts   = payload.split('>>', 1)
            pattern = parts[0].strip()
            target  = parts[1].strip() if len(parts) > 1 else '.'
            message = _run_grep(pattern, target)

        elif "edit" in name_l:
            seg = payload.split('||')
            if len(seg) < 3:
                message = "❌ EDIT: Formato inválido. Use: arquivo.py || old: texto antigo || new: texto novo"
            else:
                filename = seg[0].strip()
                old_text = re.sub(r'^old:\s*', '', seg[1].strip())
                new_text = re.sub(r'^new:\s*', '', seg[2].strip())
                message  = _run_edit(filename, old_text, new_text)

        elif "write" in name_l:
            file_match = re.search(r'([\w\./\\]+\.\w+)', payload)
            filename   = file_match.group(1) if file_match else "INFO.txt"
            content    = payload.replace(filename, "").strip(": ")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            message = f"✅ SUCESSO: Arquivo '{filename}' criado/sobrescrito em {os.getcwd()}"

        elif "todo" in name_l:
            file_match = re.search(r'([\w\./\\]+\.\w+)', payload)
            filename   = file_match.group(1) if file_match else "TODO.txt"
            content    = payload.replace(filename, "").strip(": ")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            message = f"✅ SUCESSO: Arquivo '{filename}' atualizado em {os.getcwd()}"

        else:
            message = f"📡 Simulação: {name} recebeu '{payload}'"

    except Exception as e:
        message = f"❌ ERRO DE SISTEMA: {str(e)}"

    return ToolExecution(
        name=module.name, source_hint=module.source_hint,
        payload=payload, handled=True, message=message
    )


def get_tools(simple_mode=False, include_mcp=True, permission_context=None):
    return PORTED_TOOLS

def build_tool_backlog():
    return PortingBacklog(title='Tool surface', modules=list(PORTED_TOOLS))

def find_tools(query, limit=20):
    return [m for m in PORTED_TOOLS if query.lower() in m.name.lower()][:limit]