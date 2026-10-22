# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=2,<3", "httpx>=0.27", "youtube-transcript-api>=1.2,<2"]
# ///
"""Servidor MCP que permite a Claude leer la transcripción de videos de YouTube."""

import asyncio
import re
from urllib.parse import parse_qs, urlparse

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
    YouTubeTranscriptApiException,
)

mcp = MCPServer("youtube")

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _video_id(url_or_id: str) -> str:
    value = url_or_id.strip()
    if _ID_RE.match(value):
        return value
    parsed = urlparse(value if "://" in value else "https://" + value)
    host = (parsed.hostname or "").removeprefix("www.").removeprefix("m.")
    if host == "youtu.be":
        candidate = parsed.path.lstrip("/").split("/")[0]
    elif host.endswith("youtube.com") or host == "youtube-nocookie.com":
        candidate = parse_qs(parsed.query).get("v", [""])[0]
        if not candidate:
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2 and parts[0] in ("shorts", "embed", "live", "v"):
                candidate = parts[1]
    else:
        candidate = ""
    if not _ID_RE.match(candidate):
        raise ToolError(f"No reconozco un video de YouTube en: {url_or_id}")
    return candidate


def _timestamp(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


async def _title(video_id: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://www.youtube.com/oembed",
                params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            )
        if r.status_code == 200:
            data = r.json()
            return f"{data.get('title')} — {data.get('author_name')}"
    except httpx.HTTPError:
        pass
    return None


def _fetch(video_id: str, languages: list[str]):
    transcripts = YouTubeTranscriptApi().list(video_id)
    try:
        transcript = transcripts.find_transcript(languages)
    except NoTranscriptFound:
        # Sin subtítulos en los idiomas pedidos: se toma el primero disponible.
        transcript = next(iter(transcripts))
    return transcript.fetch()


@mcp.tool()
async def youtube_transcript(
    url: str,
    languages: list[str] | None = None,
    timestamps: bool = True,
) -> str:
    """Obtiene el título y la transcripción (lo que se dice) de un video de YouTube.

    Úsala cuando el usuario comparta un enlace de YouTube y quiera que lo expliques,
    resumas o respondas preguntas sobre él. Solo incluye el audio transcrito, no lo
    que se ve en pantalla.

    Args:
        url: Enlace del video (watch, youtu.be, shorts, live, embed) o su ID de 11 caracteres.
        languages: Idiomas preferidos en orden, p. ej. ["es", "en"]. Si no hay ninguno, usa el primero disponible.
        timestamps: Si es True, agrupa el texto en bloques de unos 30 s con su marca de tiempo.
    """
    video_id = _video_id(url)
    try:
        fetched = await asyncio.to_thread(_fetch, video_id, languages or ["es", "en"])
    except TranscriptsDisabled as e:
        raise ToolError("Este video no tiene subtítulos ni transcripción disponibles.") from e
    except VideoUnavailable as e:
        raise ToolError("El video no existe o no está disponible.") from e
    except StopIteration as e:
        raise ToolError("El video no tiene ninguna transcripción.") from e
    except YouTubeTranscriptApiException as e:
        raise ToolError(f"YouTube rechazó la petición: {type(e).__name__}") from e

    lines = []
    if timestamps:
        block_start, block = None, []
        for snippet in fetched.snippets:
            if block_start is None:
                block_start = snippet.start
            block.append(snippet.text.replace("\n", " "))
            if snippet.start - block_start >= 30:
                lines.append(f"[{_timestamp(block_start)}] {' '.join(block)}")
                block_start, block = None, []
        if block:
            lines.append(f"[{_timestamp(block_start)}] {' '.join(block)}")
    else:
        lines.append(" ".join(s.text.replace("\n", " ") for s in fetched.snippets))

    title = await _title(video_id)
    kind = "automática" if fetched.is_generated else "manual"
    header = [
        f"Video: https://www.youtube.com/watch?v={video_id}",
        *([f"Título: {title}"] if title else []),
        f"Transcripción {kind} en {fetched.language} ({fetched.language_code})",
        "",
    ]
    return "\n".join(header + lines)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
