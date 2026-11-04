# tawler

Paste a link, take the file. Video, audio, GIF or a trimmed clip from every site the installed
yt-dlp knows (1,751 extractors at build time). Nothing is written to disk and nothing is stored
after a request ends.

## Stack

- `api/` FastAPI + yt-dlp + ffmpeg. Probes links, signs media tickets, pipes bytes to the response.
- `web/` Next.js 16 App Router, Tailwind v4, hand-built components. No UI kit, no database.

## Run locally

```bash
# api
cd api
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python fastapi "uvicorn[standard]" yt-dlp httpx pydantic-settings
PYTHONPATH=src .venv/bin/python -m uvicorn tawler.main:app --port 8010

# web
cd web
npm install
API_ORIGIN=http://127.0.0.1:8010 npm run dev -p 3100
```

Open `http://localhost:3100`. Port 8000 and 3000 are commonly taken on shared hosts, which is why
the defaults here are 8010 and 3100.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | extractor count, readiness |
| GET | `/api/sites` | full extractor list, optional `?q=` |
| GET | `/api/match?url=` | which extractor claims a URL |
| POST | `/api/probe` | metadata, formats, subtitles, per-format tickets |
| GET | `/api/preview/{ticket}` | range-aware media proxy for the player |
| GET | `/api/dl/{ticket}` | file download, `?start=&end=` to trim, `?to=mp3` to convert |
| GET | `/api/gif/{ticket}` | animated GIF, `?start=&end=&width=&fps=` |
| GET | `/api/thumb/{ticket}` | cover art |
| GET | `/api/sub/{ticket}` | subtitle file |

## Design constraints

**No storage.** There is no database and no temp directory. A probe returns signed tickets that
carry the resolved media URL, headers and filename. Downloads are either a straight range proxy or
an ffmpeg pipe into the response body.

**One worker.** Concurrency limits and the fallback ticket key live in process. Scale by raising
`TAWLER_MAX_DOWNLOADS`, not by adding workers, unless you set `TAWLER_SECRET` and move the limiter
to a shared store.

**HLS sources.** A preview only uses progressive (`http`/`https`) formats, because browsers cannot
play `m3u8` natively. HLS-only items show cover art instead of a player and still download fine,
since ffmpeg reads the playlist directly.

**YouTube.** Datacenter IPs get "Sign in to confirm you're not a bot" on every player client. Set
`TAWLER_COOKIES_FILE` to a Netscape `cookies.txt` from an account that can watch the content. This
is a yt-dlp and IP reputation matter, not a bug in this code.

## Deploy

Coolify, **Docker Compose** build pack, compose location `/compose.coolify.yml`. Railpack is the
wrong pack here: it builds one service from source, and ffmpeg would depend on it guessing a system
package.

Set `TAWLER_SECRET` and `TAWLER_PUBLIC_ORIGIN` in the service environment, then add two domains on
the same hostname:

| Domain | Service | Port | Path |
| --- | --- | --- | --- |
| `https://<host>` | web | 3000 | `/` |
| `https://<host>` | api | 8000 | `/api` |

Both containers share the Compose network, so the web app reaches the API at `http://api:8000`. Do
not add Traefik labels to the compose file: Coolify generates them from the domain table, and
duplicates make the router ambiguous.

### Mounted under a path

If the app is served from a path rather than a hostname (`https://host/tawler`), set
`NEXT_PUBLIC_BASE_PATH=/tawler` **before building**. It is compiled into the client bundle, so
changing it requires a redeploy, not a restart. Assets and the `/api` proxy both follow the prefix
because the proxy is an app route (`web/src/app/api/[...path]/route.ts`), not a rewrite: Next 16
prefixes rewrite sources with `basePath` but matches them after stripping it, so rewrites 404 under
a subpath.

## Legal

The tool is a pipe. What passes through it is the operator's and the user's responsibility.
