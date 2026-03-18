"""Adaptador para análise de vídeo via MCP zai-analyze-video."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from ..domain.transcript import Transcript, TranscriptSegment


class VideoAnalyzerAdapter:
    """
    Adaptador para MCP zai-analyze-video.

    Funcionalidades:
        - Transcrição de áudio
        - Extração de key moments
        - Geração de resumos
    """

    def __init__(self, claude_tool_call=None):
        """
        Args:
            claude_tool_call: Função para chamar tools do Claude (ex: mcp__zai-mcp-server__analyze_video)
        """
        self._claude_tool_call = claude_tool_call

    async def transcribe(
        self,
        video_path: Path | str,
        language: str = "auto",
    ) -> Optional[Transcript]:
        """
        Transcreve o áudio do vídeo.

        Args:
            video_path: Caminho local para o vídeo
            language: Código do idioma (pt, en, auto)

        Returns:
            Transcript com segmentos e timestamps
        """
        analysis = await self._analyze_video(
            video_path,
            "Transcreva o áudio deste vídeo e retorne apenas a transcrição completa, sem formatação adicional."
        )

        if not analysis:
            return None

        # Extrair a transcrição da análise
        transcript_text = analysis.get("transcription", "")
        if not transcript_text:
            # Tentar extrair do texto completo
            full_text = analysis.get("full_text", "")
            transcript_text = full_text

        # Criar segmentos simples (sem timestamps detalhados)
        # TODO: Melhorar para extrair timestamps reais
        segments = self._create_simple_segments(transcript_text)

        return Transcript(
            video_id=str(video_path),
            segments=segments,
            language=language,
        )

    async def analyze(
        self,
        video_path: Path | str,
        prompt: str = "Describe the key moments and insights from this video",
    ) -> Dict:
        """
        Analisa o vídeo e extrai insights.

        Args:
            video_path: Caminho para o vídeo
            prompt: Prompt para a análise

        Returns:
            Dict com key_moments, summary, topics
        """
        return await self._analyze_video(video_path, prompt)

    async def _analyze_video(self, video_path: Path | str, prompt: str) -> Optional[Dict]:
        """Chama o MCP Analyzer."""
        if not self._claude_tool_call:
            print("WARNING: No claude_tool_call provided, returning mock analysis")
            return self._mock_analysis()

        try:
            # Chamar o tool MCP
            result = await self._claude_tool_call(
                "mcp__zai-mcp-server__analyze_video",
                video_source=str(video_path),
                prompt=prompt,
            )
            return self._parse_analysis_result(result)
        except Exception as e:
            print(f"ERROR analyzing video: {e}")
            return None

    def _parse_analysis_result(self, result: str) -> Dict:
        """Parse o resultado do MCP Analyzer."""
        if not result:
            return {}

        # Tentar extrair informações estruturadas do texto
        return {
            "full_text": result,
            "transcription": self._extract_transcription(result),
            "summary": self._extract_summary(result),
            "key_moments": self._extract_key_moments(result),
            "topics": self._extract_topics(result),
            "insights": self._extract_insights(result),
        }

    def _extract_transcription(self, text: str) -> str:
        """Extrai a seção de transcrição."""
        # Padrões comuns de marcação
        patterns = [
            r"## Transcrição Completa\s*\n+(.*?)(?=\n+##|\n+---|\Z)",
            r"###?\s*Transcrição\s*:\s*\n+(.*?)(?=\n+###|\n+##|\Z)",
            r"1\)\s*Transcrição\s*.*?\n+(.*?)(?=\n+2\)|\n+##|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_summary(self, text: str) -> str:
        """Extrai o resumo."""
        patterns = [
            r"## Resumo do Conteúdo\s*\n+(.*?)(?=\n+##|\n+---|\Z)",
            r"2\)\s*Resumo\s*.*?\n+(.*?)(?=\n+3\)|\n+##|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_key_moments(self, text: str) -> List[Dict]:
        """Extrai key moments com timestamps."""
        moments = []

        # Padrão de tabela ou lista de timestamps
        # | **0:00 - 0:15** | Descrição |
        table_pattern = r'\|\s*\*\*(\d+:\d+)\s*-\s*(\d+:\d+)\s*\*\*\s*\|\s*([^|]+)\s*\|'
        for match in re.finditer(table_pattern, text):
            start_time = match.group(1)
            end_time = match.group(2)
            description = match.group(3).strip()
            moments.append({
                "start_time": start_time,
                "end_time": end_time,
                "description": description,
            })

        return moments

    def _extract_topics(self, text: str) -> List[str]:
        """Extrai tags/tópicos."""
        patterns = [
            r"## Tópicos/Tags.*?\n+(.*?)(?=\n+##|\n+---|\Z)",
            r"4\)\s*Tópicos.*?\n+(.*?)(?=\n+5\)|\n+##|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                content = match.group(1).strip()
                # Extrair itens de lista ou tags
                topics = re.findall(r'-\s*`([^`]+)`|-\s*([^-\n]+)', content)
                return [t[0] or t[1] for t in topics]

        return []

    def _extract_insights(self, text: str) -> List[str]:
        """Extrai insights/aprendizados."""
        patterns = [
            r"## Insights.*?\n+(.*?)(?=\n+##|\n+---|\Z)",
            r"5\)\s*Insights.*?\n+(.*?)(?=\n+##|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                content = match.group(1).strip()
                # Extrair itens numerados
                insights = re.findall(r'###?\s*\d+\.\s*(.*?)(?=\n+###?\s*\d+\.|\n+##|\Z)', content, re.DOTALL)
                return [i.strip() for i in insights]

        return []

    def _create_simple_segments(self, text: str) -> List[TranscriptSegment]:
        """Cria segmentos simples a partir do texto."""
        if not text:
            return []

        # Dividir em parágrafos
        paragraphs = re.split(r'\n\n+', text.strip())
        segments = []
        current_time = 0.0

        for para in paragraphs:
            if not para.strip():
                continue
            # Estimar duração baseada no tamanho do parágrafo
            # ~150 palavras por minuto = 2.5 palavras por segundo
            word_count = len(para.split())
            duration = max(2.0, word_count / 2.5)

            segments.append(TranscriptSegment(
                start_time=current_time,
                end_time=current_time + duration,
                text=para.strip(),
            ))
            current_time += duration

        return segments

    def _mock_analysis(self) -> Dict:
        """Análise mock para testes sem MCP."""
        return {
            "full_text": "Análise mock - integração MCP necessária",
            "transcription": "",
            "summary": "Mock summary",
            "key_moments": [],
            "topics": [],
            "insights": [],
        }
