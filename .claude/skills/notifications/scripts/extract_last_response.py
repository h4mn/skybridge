#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrai a última resposta do assistant do transcript
Usado pelo hook de notificação para capturar o resumo final
"""
import json
import sys
import os
from pathlib import Path
import re

# Forçar UTF-8
if sys.platform == "win32":
    import io
    if hasattr(sys.stdin, 'buffer'):
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def get_last_assistant_response(transcript_path):
    """
    Lê o transcript e retorna a última mensagem do assistant
    que NÃO seja apenas tool_use (tem texto real)
    """
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Ler de trás para frente (últimas mensagens primeiro)
        for line in reversed(lines):
            try:
                entry = json.loads(line.strip())
                message = entry.get("message", {})

                # Verifica se é mensagem do assistant
                if message.get("role") == "assistant":
                    content = message.get("content", [])

                    # Extrai texto não-tool_use
                    text_parts = []
                    for part in content:
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", ""))

                    if text_parts:
                        # Combina todos os textos
                        full_text = "".join(text_parts).strip()

                        # Limita tamanho (máx 500 chars para notificação)
                        if len(full_text) > 500:
                            full_text = full_text[:497] + "..."

                        return full_text

            except (json.JSONDecodeError, KeyError):
                continue

        return None  # Nenhuma resposta textual encontrada

    except Exception as e:
        print(f"ERRO lendo transcript: {e}", file=sys.stderr)
        return None

def main():
    # Lê stdin (payload do hook)
    try:
        input_data = sys.stdin.read()
        if not input_data:
            input_data = "{}"
        payload = json.loads(input_data)
    except:
        payload = {}

    # Pega transcript_path do payload
    transcript_path = payload.get("transcript_path")
    if not transcript_path:
        print("ERRO: transcript_path não encontrado no payload", file=sys.stderr)
        sys.exit(1)

    # Extrai última resposta
    last_response = get_last_assistant_response(transcript_path)

    if last_response:
        # Output para o notify_discord.py
        output = {
            "message": last_response,
            "notification_type": "info",
            "session_data": payload  # Passa todos os dados do payload
        }
        print(json.dumps(output))
    else:
        # Sem resposta textual - usa mensagem padrão
        output = {
            "message": "✅ Tarefa concluída",
            "notification_type": "success",
            "session_data": payload
        }
        print(json.dumps(output))

if __name__ == "__main__":
    main()
