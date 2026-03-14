#!/usr/bin/env python3
"""
Servidor TTS Persistente - Kokoro

Mantém o modelo Kokoro carregado em memória para evitar cold start.
Comunica via stdin/stdout com protocolo JSON simples.

Uso:
    python scripts/tts_server.py

Protocolo:
    Entrada: {"text": "Olá", "voice": "af_heart", "lang_code": "p"}
    Saída:   {"status": "ok", "duration": 1.5, "sample_rate": 24000, "size": 144000}
    Erro:    {"status": "error", "message": "..."}

O áudio é salvo em arquivo temporário e o caminho é retornado.
"""

import sys
import os
import json
import tempfile
import time
import numpy as np

# Adiciona src ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


class TTSServer:
    """Servidor TTS com modelo persistente."""

    def __init__(self, default_voice="af_heart", default_lang="p"):
        """Inicializa servidor."""
        self.default_voice = default_voice
        self.default_lang = default_lang
        self.pipeline = None
        self._load_count = 0

    def load_model(self):
        """Carrega modelo Kokoro (uma única vez)."""
        if self.pipeline is None:
            print(f"[SERVER] Carregando Kokoro...", file=sys.stderr)
            start = time.perf_counter()

            from kokoro import KPipeline
            self.pipeline = KPipeline(lang_code=self.default_lang)

            load_time = time.perf_counter() - start
            print(f"[SERVER] Modelo carregado em {load_time*1000:.1f}ms", file=sys.stderr)
            print(f"[SERVER] Pronto para sintetizar!", file=sys.stderr)

            # Envia confirmação
            self._respond({
                "status": "ready",
                "load_time_ms": load_time * 1000,
                "voice": self.default_voice,
                "lang": self.default_lang
            })

    def synthesize(self, text, voice=None, lang_code=None, speed=1.0):
        """Sintetiza texto."""
        voice = voice or self.default_voice
        lang_code = lang_code or self.default_lang

        try:
            start = time.perf_counter()

            # Gera áudio
            generator = self.pipeline(
                text,
                voice=voice,
                speed=speed,
                split_pattern=r'\n+'
            )

            audio_array = None
            for gs, ps, audio in generator:
                audio_array = audio

            if audio_array is None:
                raise RuntimeError("Falha ao gerar áudio")

            # Converte Tensor para numpy se necessário
            if hasattr(audio_array, 'cpu'):
                audio_array = audio_array.cpu().numpy()

            # Normaliza
            if audio_array.dtype != np.float32:
                audio_array = audio_array.astype(np.float32)

            if np.max(np.abs(audio_array)) > 0:
                audio_array = audio_array / np.max(np.abs(audio_array))

            # Salva em arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.wav',
                delete=False,
                mode='wb'
            )

            # Converte para bytes e escreve
            audio_bytes = (audio_array * 0.8).astype(np.float32).tobytes()
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
            temp_file.close()

            synth_time = time.perf_counter() - start
            duration = len(audio_array) / 24000  # Kokoro usa 24000 Hz

            return {
                "status": "ok",
                "audio_file": temp_file_path,
                "duration": duration,
                "sample_rate": 24000,
                "size": len(audio_bytes),
                "synth_time_ms": synth_time * 1000
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _respond(self, data):
        """Envia resposta JSON para stdout."""
        print(json.dumps(data))
        sys.stdout.flush()

    def run(self):
        """Loop principal do servidor."""
        print(f"[SERVER] Iniciando servidor TTS...", file=sys.stderr)

        # Carrega modelo
        self.load_model()

        print(f"[SERVER] Aguardando requisições via stdin...", file=sys.stderr)

        # Loop de processamento
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)

                if request.get("action") == "synthesize":
                    result = self.synthesize(
                        text=request.get("text", ""),
                        voice=request.get("voice"),
                        lang_code=request.get("lang_code"),
                        speed=request.get("speed", 1.0)
                    )
                    self._respond(result)

                elif request.get("action") == "quit":
                    print(f"[SERVER] Encerrando...", file=sys.stderr)
                    break

                else:
                    self._respond({
                        "status": "error",
                        "message": f"Ação desconhecida: {request.get('action')}"
                    })

            except json.JSONDecodeError as e:
                self._respond({
                    "status": "error",
                    "message": f"JSON inválido: {e}"
                })
            except Exception as e:
                self._respond({
                    "status": "error",
                    "message": str(e)
                })


def main():
    """Entry point."""
    server = TTSServer(default_voice="af_heart", default_lang="p")
    try:
        server.run()
    except KeyboardInterrupt:
        print(f"\n[SERVER] Interrompido", file=sys.stderr)
    finally:
        print(f"[SERVER] Servidor encerrado", file=sys.stderr)


if __name__ == "__main__":
    main()
