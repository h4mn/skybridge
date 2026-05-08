"""Renova o refresh token OAuth do YouTube e busca os 10 ultimos favoritos."""

import os
import sys
import webbrowser
import requests
import urllib.parse
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

client_id = os.getenv("YOUTUBE_CLIENT_ID")
client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")

if not client_id or not client_secret:
    print("ERROR: YOUTUBE_CLIENT_ID e YOUTUBE_CLIENT_SECRET nao encontrados no .env")
    sys.exit(1)

params = urllib.parse.urlencode({
    "client_id": client_id,
    "redirect_uri": "http://localhost",
    "response_type": "code",
    "scope": "https://www.googleapis.com/auth/youtube.readonly",
    "access_type": "offline",
    "prompt": "consent",
})
url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"

print("Abrindo browser para autorizacao...")
webbrowser.open(url)
print(f"\nURL (caso nao abra automaticamente):\n{url}\n")
print("Apos autorizar, o browser vai redirecionar para localhost (vai dar erro, normal).")
print("Copie o parametro CODE da URL e cole abaixo.")
print("Exemplo: http://localhost/?code=4/0AY0e-g7XXXXX&scope=...")
print()

code = input("Cole o code aqui: ").strip()

resp = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": client_id,
    "client_secret": client_secret,
    "code": code,
    "redirect_uri": "http://localhost",
    "grant_type": "authorization_code",
})
data = resp.json()

if "refresh_token" not in data:
    print(f"\nErro ao obter tokens: {data}")
    sys.exit(1)

new_refresh = data["refresh_token"]
print(f"\nNovo refresh token obtido!")

env_path = project_root / ".env"
content = env_path.read_text(encoding="utf-8")
lines = content.split("\n")
updated = False
new_lines = []
for line in lines:
    if line.startswith("YOUTUBE_REFRESH_TOKEN="):
        new_lines.append(f"YOUTUBE_REFRESH_TOKEN={new_refresh}")
        updated = True
    else:
        new_lines.append(line)
if not updated:
    new_lines.append(f"YOUTUBE_REFRESH_TOKEN={new_refresh}")

env_path.write_text("\n".join(new_lines), encoding="utf-8")
print(".env atualizado!")

access_token = data["access_token"]
from core.youtube.infrastructure.youtube_api_client import YouTubeAPIClient
client = YouTubeAPIClient(access_token)
videos = client.get_playlist_items(playlist_id="LL", max_results=10)

print(f"\n{len(videos)} ultimos favoritos:\n")
for i, v in enumerate(videos, 1):
    dur = v.get("duration_seconds")
    if dur:
        m, s = divmod(dur, 60)
        h, m = divmod(m, 60)
        dur_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    else:
        dur_str = "???"
    title = v["title"][:55] + "..." if len(v["title"]) > 55 else v["title"]
    print(f"  {i:2d}. [{dur_str}] {title}")
    print(f"      Canal: {v['channel']}")
    print(f"      ID: {v['video_id']}")
    print()
