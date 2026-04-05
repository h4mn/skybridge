import json
import sys
import io
import time

# Forçar UTF-8 no output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Cores ANSI
RESET = "\033[0m"
AZUL_BOLD = "\033[1;34m"
LARANJA_BOLD = "\033[1;38;5;208m"
VERDE = "\033[32m"
LARANJA = "\033[33m"
VERMELHO = "\033[31m"
BRANCO = "\033[37m"
CINZA_ESCURO = "\033[90m"

# Gradiente Sky (azul → violeta) - cores RGB vibrantes
SKY_GRADIENT = [
    "\033[38;2;59;130;246;1m",    # Azul vibrante (#3B82F6)
    "\033[38;2;99;102;241;1m",    # Índigo (#6366F1)
    "\033[38;2;139;92;246;1m",    # Violeta (#8B5CF6)
    "\033[38;2;168;85;247;1m",    # Roxo (#A855F7)
    "\033[38;2;192;132;252;1m",   # Lavanda (#C084FC)
    "\033[38;2;217;70;239;1m",    # Fúcsia (#D946EF)
]

data = json.load(sys.stdin)

# Campos
model = data.get('model', {}).get('display_name', 'N/A')
version = data.get('version', 'N/A')
cwd = data.get('cwd', '')

# Contexto usado
ctx = data.get('context_window', {})
used_pct = ctx.get('used_percentage', 0)

# Cor baseada no uso: verde <= 50%, laranja < 70%, vermelho >= 70%
if used_pct <= 50:
    ctx_color = VERDE
elif used_pct < 70:
    ctx_color = LARANJA
else:
    ctx_color = VERMELHO

# Parte dinâmica do cwd
project = data.get('workspace', {}).get('project_dir', '')
if project and cwd.startswith(project):
    # Remove o prefixo do projeto
    dynamic = cwd.replace(project, '').lstrip('\\').lstrip('/')
    # Se ficou vazio (está na raiz do projeto), mostra o nome do projeto
    if not dynamic:
        # Extrai o nome do projeto do caminho
        dynamic = project.replace('\\', '/').split('/')[-1]
else:
    parts = cwd.replace('\\', '/').split('/')
    if len(parts) > 2:
        dynamic = '.../' + '/'.join(parts[-2:])
    else:
        dynamic = cwd

# Animação do gradiente - roda as cores com o tempo
anim_offset = int(time.time() * 2) % len(SKY_GRADIENT)  # Muda 2x por segundo
sky_s = SKY_GRADIENT[(anim_offset) % len(SKY_GRADIENT)]
sky_k = SKY_GRADIENT[(anim_offset + 1) % len(SKY_GRADIENT)]
sky_y = SKY_GRADIENT[(anim_offset + 2) % len(SKY_GRADIENT)]

# 🤖 Sky v2.1.89 [GLM-4.7] | 28% | Hadsteca
sky_name = f"{sky_s}S{sky_k}k{sky_y}y{RESET}"
print(f"🤖 {sky_name} v{LARANJA_BOLD}{version}{RESET} [{CINZA_ESCURO}{model}{RESET}] | {ctx_color}{used_pct}%{RESET} | {BRANCO}{dynamic}{RESET}")
