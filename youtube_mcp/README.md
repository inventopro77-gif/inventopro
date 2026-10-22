# YouTube como herramienta de Claude (MCP)

Servidor MCP con una herramienta, `youtube_transcript`, que obtiene el título y la
transcripción de un video de YouTube para que Claude pueda explicarlo, resumirlo o
responder preguntas sobre él.

> Solo lee **lo que se dice** (subtítulos manuales o automáticos). Lo que se ve en
> pantalla no está incluido: para eso, manda capturas a Claude.

## Requisito

[uv](https://docs.astral.sh/uv/getting-started/installation/). Las dependencias se instalan
solas la primera vez.

- macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

Después cierra y vuelve a abrir la terminal para que `uv` quede disponible.

## Claude Desktop

1. Abre **Ajustes → Desarrollador → Editar configuración**. Se abre `claude_desktop_config.json`:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
2. Pega esto (cambia las rutas por las tuyas; usa rutas completas):

   ```json
   {
     "mcpServers": {
       "youtube": {
         "command": "/ruta/completa/a/uv",
         "args": ["run", "--script", "/ruta/a/inventopro/youtube_mcp/server.py"]
       }
     }
   }
   ```

   - Ruta de `uv`: `which uv` (macOS/Linux) o `where uv` (Windows).
   - En Windows escribe las barras dobles: `"C:\\Users\\tu\\inventopro\\youtube_mcp\\server.py"`.
   - Si ya tienes otros servidores en `mcpServers`, añade `"youtube"` junto a ellos.
3. Cierra Claude Desktop por completo y vuelve a abrirlo.
4. En el chat, el icono de herramientas debe mostrar `youtube_transcript`.
5. Pega un enlace: *"explícame este video: https://youtu.be/..."*.

## Claude Code

Dentro de este repositorio ya está en `.mcp.json`. Para todos tus proyectos:

```bash
claude mcp add youtube --scope user -- uv run --script /ruta/a/inventopro/youtube_mcp/server.py
```

## Problemas comunes

- **"no tiene subtítulos"**: el video no tiene transcripción; no hay texto que leer.
- **`RequestBlocked` / `IpBlocked`**: YouTube bloquea algunas IPs (VPN, servidores en la nube).
  Desde una conexión doméstica normal suele funcionar.
- **El servidor no aparece en Claude Desktop**: revisa que las rutas sean completas y mira
  los logs en Ajustes → Desarrollador.
