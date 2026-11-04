# Architecture

## The short version

A probe is a read. A download is a pipe. Nothing is ever persisted.

```
browser ──POST /api/probe──▶ yt-dlp extract_info(download=False)
                                  │
                                  ├─ metadata (title, duration, cover, subtitles)
                                  └─ formats[] each with a signed ticket
                                          │
browser ──GET /api/dl/{ticket}────────────┴──▶ range proxy (progressive)
                                            └─ ffmpeg pipe (merge, trim, convert)
```

## Why tickets instead of a job store

A downloader needs the browser to hit the media URL, but handing out raw URLs turns the API into an
open proxy and leaks signed CDN links. Instead every URL is wrapped in an HMAC ticket:

```
base64url(zlib(json{ u, h, n, x, p, a, e })) + "." + hmac_sha256[:24]
```

`u` media URL, `h` request headers, `n` filename, `x` container, `p` protocol, `a` companion audio
URL, `e` expiry. The API refuses any request whose ticket does not verify, so it can only ever fetch
URLs it minted itself, and they expire.

There is no job table. Two tabs, a restart, or a second browser do not share state, and nothing
needs cleaning up.

## The three download paths

| Source | Path | Cost |
| --- | --- | --- |
| single muxed file, no trim | range proxy via httpx | no CPU, resumable |
| separate video + audio | `ffmpeg -i v -i a -c copy` to fragmented MP4 | copy only, no transcode |
| trim, convert, GIF | ffmpeg filter or encoder to stdout | CPU bound, capped at 4 concurrent |

Fragmented MP4 (`+frag_keyframe+empty_moov`) is what makes the second and third paths streamable:
the moov atom is at the front and no seeking is required, so ffmpeg can write to a pipe.

The trade-off is honest: fragmented output has no `Content-Length`, so no resume and no exact
progress percentage. Direct proxies keep both.

## Why previews filter on protocol

`preview` is chosen only from formats whose protocol is `http` or `https`. Browsers do not play HLS
playlists, so an `m3u8` URL in a `<video>` tag renders a dead player. When nothing progressive
exists, the UI shows cover art and the item remains fully downloadable.

## Concurrency

Two `anyio.CapacityLimiter`s: 8 probes, 4 pipes. Probes run in a worker thread because yt-dlp is
blocking; pipes are `asyncio.create_subprocess_exec` with a 64 KiB first-chunk read so a bad
command fails before headers are sent.

If the first chunk never arrives, the route returns `502` with ffmpeg's last stderr line instead of
an empty `200`. That distinction is what keeps failures debuggable.

## MCP

`/api/mcp` is a Streamable HTTP MCP server mounted on the same FastAPI app, so it inherits the same
`/api` rewrite the browser uses and needs no extra routing.

```
client ──POST /api/mcp──▶ BearerGuard ──▶ MCPServer (stateless, JSON response)
                                              │
                                              └─ tools call the same core.ytdlp functions
                                                 and return absolute signed URLs
```

Three details worth knowing before changing it:

- **Mount point.** The app is mounted at `/api` with the inner route at `/mcp`. Mounting at
  `/api/mcp` with an inner route of `/` makes Starlette emit a 307 to the trailing slash, and MCP
  clients do not reliably follow redirects on POST.
- **Lifespan.** `StreamableHTTPSessionManager` only exists after `streamable_http_app()` is called,
  and its task group must be started from the host app's lifespan. `mcp_lifespan()` does that;
  dropping it produces "Task group is not initialized" on the first request.
- **Auth.** `BearerGuard` wraps the mount and rejects anything without `TRAWLER_MCP_TOKEN`. When the
  token is empty the mount is not created at all, so there is no unauthenticated path.

Tools never move bytes. `probe` and the link tools mint tickets through `core.tickets` and return
absolute URLs built from `TRAWLER_PUBLIC_ORIGIN`; the client fetches those over plain HTTP.

## Deliberate omissions

- No auth, no accounts, no history.
- No CDN cache in front of `/api`: tickets are per-request and streams are large.
- No queue: requests are the queue. A slow item holds one of four pipe slots and nothing else.
- No database: if you need analytics, put them in the reverse proxy log, not in this app.
