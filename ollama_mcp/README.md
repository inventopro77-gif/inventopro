# Ollama como herramienta de Claude (MCP)

Servidor MCP que deja a Claude (Claude Code, Claude Desktop o cualquier cliente MCP)
llamar a los modelos de tu Ollama local.

## Herramientas

| Herramienta          | Qué hace                                                     |
|----------------------|--------------------------------------------------------------|
| `ollama_list_models` | Lista los modelos instalados (`/api/tags`).                  |
| `ollama_chat`        | Envía un prompt a un modelo local y devuelve la respuesta.   |
| `ollama_embed`       | Devuelve el embedding de un texto (`nomic-embed-text` por defecto). |

## Requisitos

- [Ollama](https://ollama.com) corriendo (`ollama serve`) y al menos un modelo: `ollama pull llama3.2`
- [uv](https://docs.astral.sh/uv/) — instala las dependencias (`mcp`, `httpx`) solo, en la primera ejecución.

## Uso con Claude Code

Dentro de este repositorio no hay que hacer nada: el archivo `.mcp.json` de la raíz
registra el servidor. Abre `claude` aquí, acepta el servidor `ollama` cuando lo pregunte
y compruébalo con `/mcp`.

Para tenerlo en **todos** tus proyectos:

```bash
claude mcp add ollama --scope user \
  -e OLLAMA_DEFAULT_MODEL=llama3.2 \
  -- uv run --script /ruta/a/inventopro/ollama_mcp/server.py
```

Después pídele cosas como: *"usa ollama para resumir este archivo"* o
*"pregúntale a qwen3 en ollama qué opina de esta función"*.

## Uso con Claude Desktop

En `claude_desktop_config.json` (Ajustes → Desarrollador → Editar configuración):

```json
{
  "mcpServers": {
    "ollama": {
      "command": "uv",
      "args": ["run", "--script", "/ruta/a/inventopro/ollama_mcp/server.py"],
      "env": { "OLLAMA_DEFAULT_MODEL": "llama3.2" }
    }
  }
}
```

Si Claude Desktop no encuentra `uv`, pon la ruta completa (`which uv`).

## Variables de entorno

| Variable               | Por defecto              |
|------------------------|--------------------------|
| `OLLAMA_HOST`          | `http://localhost:11434` |
| `OLLAMA_DEFAULT_MODEL` | `llama3.2`               |
| `OLLAMA_TIMEOUT`       | `300` (segundos)         |

## Nota sobre Claude Code en la web

Las sesiones de Claude Code en la nube corren en un contenedor remoto y **no** ven el
`localhost` de tu computadora. Para usar esta herramienta ahí tendrías que exponer Ollama
en una URL pública (con autenticación) y apuntar `OLLAMA_HOST` a ella. Lo normal es usarla
con Claude Code o Claude Desktop en tu propia máquina.
