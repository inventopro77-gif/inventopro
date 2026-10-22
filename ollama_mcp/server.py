# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=2,<3", "httpx>=0.27"]
# ///
"""Servidor MCP que expone un Ollama local como herramientas para Claude.

Variables de entorno:
  OLLAMA_HOST           URL de Ollama (por defecto http://localhost:11434)
  OLLAMA_DEFAULT_MODEL  modelo usado si la llamada no indica uno (por defecto llama3.2)
  OLLAMA_TIMEOUT        segundos máximos por petición (por defecto 300)
"""

import os

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
if not OLLAMA_HOST.startswith(("http://", "https://")):
    OLLAMA_HOST = "http://" + OLLAMA_HOST
DEFAULT_MODEL = os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3.2")
TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "300"))

mcp = MCPServer("ollama")


async def _request(method: str, path: str, json: dict | None = None) -> dict:
    try:
        async with httpx.AsyncClient(base_url=OLLAMA_HOST, timeout=TIMEOUT) as client:
            response = await client.request(method, path, json=json)
    except httpx.ConnectError as e:
        raise ToolError(
            f"No se pudo conectar con Ollama en {OLLAMA_HOST}. ¿Está corriendo `ollama serve`?"
        ) from e
    except httpx.TimeoutException as e:
        raise ToolError(f"Ollama no respondió en {TIMEOUT:.0f} s (ajusta OLLAMA_TIMEOUT).") from e
    if response.status_code >= 400:
        try:
            detail = response.json().get("error", response.text)
        except ValueError:
            detail = response.text
        raise ToolError(f"Ollama respondió {response.status_code}: {detail}")
    return response.json()


@mcp.tool()
async def ollama_list_models() -> str:
    """Lista los modelos instalados en el Ollama local."""
    data = await _request("GET", "/api/tags")
    models = data.get("models", [])
    if not models:
        return "No hay modelos instalados. Instala uno con `ollama pull <modelo>`."
    lines = []
    for m in models:
        size_gb = m.get("size", 0) / 1e9
        details = m.get("details", {})
        extra = ", ".join(v for v in (details.get("parameter_size"), details.get("quantization_level")) if v)
        lines.append(f"- {m['name']} ({size_gb:.1f} GB{', ' + extra if extra else ''})")
    return "\n".join(lines)


@mcp.tool()
async def ollama_chat(
    prompt: str,
    model: str | None = None,
    system: str | None = None,
    temperature: float | None = None,
) -> str:
    """Envía un prompt a un modelo local de Ollama y devuelve su respuesta.

    Útil para delegar tareas sencillas o privadas (resúmenes, traducciones,
    clasificación, borradores) a un modelo que corre en la máquina del usuario.

    Args:
        prompt: Mensaje para el modelo.
        model: Nombre del modelo (ver ollama_list_models). Si se omite, usa OLLAMA_DEFAULT_MODEL.
        system: Instrucción de sistema opcional.
        temperature: Temperatura de muestreo opcional (0 = determinista).
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload: dict = {"model": model or DEFAULT_MODEL, "messages": messages, "stream": False}
    if temperature is not None:
        payload["options"] = {"temperature": temperature}
    data = await _request("POST", "/api/chat", json=payload)
    return data.get("message", {}).get("content", "")


@mcp.tool()
async def ollama_embed(text: str, model: str = "nomic-embed-text") -> list[float]:
    """Calcula el embedding de un texto con un modelo de embeddings de Ollama.

    Args:
        text: Texto a convertir en vector.
        model: Modelo de embeddings (por defecto nomic-embed-text).
    """
    data = await _request("POST", "/api/embed", json={"model": model, "input": text})
    return data["embeddings"][0]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
